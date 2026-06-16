// Max-Value Aggregation with Constrained Shared Memory -Multiprocessing
#define _POSIX_C_SOURCE 200809L
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <limits.h>
#include <unistd.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <semaphore.h>
#include <fcntl.h>
#include <time.h>
#include <errno.h>

// timing helpers
static long long t_ns(void){
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC,&t);
    return (long long)t.tv_sec*1000000000LL + t.tv_nsec;
}
static double ns_to_ms(long long ns){ return (double)ns/1.0e6; }
static long rss_self(void){ struct rusage ru; if(getrusage(RUSAGE_SELF,&ru)!=0) return -1; return ru.ru_maxrss; }
static long rss_children(void){ struct rusage ru; if(getrusage(RUSAGE_CHILDREN,&ru)!=0) return -1; return ru.ru_maxrss; }

// fill array
static void fill_rand(int *a, size_t n, unsigned seed){
    uint32_t x=seed?seed:2463534242u;
    for(size_t i=0;i<n;i++){
        x^=x<<13; x^=x>>17; x^=x<<5;
        a[i]=(int)(x & 0x7fffffff);
    }
}

// sequential max for verification
static int seq_max(const int *a, size_t n){
    int m=a[0];
    for(size_t i=1;i<n;i++) if(a[i]>m) m=a[i];
    return m;
}

int main(int argc,char **argv){
    size_t n=131072;        // array length
    //size_t n=32; 
    unsigned seed=12345;    // RNG seed
    int verify=0;           // verify flag
    char *opt_mode=NULL;
    int opt;

    while((opt=getopt(argc,argv,"n:s:v"))!=-1){
        switch(opt){
            case 'n': n=(size_t)strtoull(optarg,NULL,10); break;
            case 's': seed=(unsigned)strtoul(optarg,NULL,10); break;
            case 'v': verify=1; break;
        }
    }

    // allocate array
    int *arr=malloc(sizeof(int)*n);
    if(!arr){ perror("malloc"); return 1; }
    fill_rand(arr,n,seed);

    // allocate shared int for global max
    int *gmax = mmap(NULL,sizeof(int),PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANONYMOUS,-1,0);
    if(gmax==MAP_FAILED){ perror("mmap"); return 1; }
    *gmax = INT_MIN;

    // semaphore
    char sem_name[64];
    snprintf(sem_name,sizeof(sem_name),"/sem_%ld",(long)getpid());
    sem_t *sem = sem_open(sem_name,O_CREAT|O_EXCL,0600,1);
    if(sem==SEM_FAILED){ perror("sem_open"); return 1; }
    sem_unlink(sem_name);

    size_t wl[]={1,2,4,8};   // worker counts to try
    size_t nwc=sizeof(wl)/sizeof(wl[0]);

    printf("Max value aggregation (process + semaphore), array size=%zu\n",n);

    for(size_t wi=0;wi<nwc;wi++){
        size_t nw=wl[wi];
        *gmax = INT_MIN;

        size_t base = n/nw;
        size_t rem  = n%nw;

        long long t0=t_ns();

        // spawn workers
        for(size_t i=0;i<nw;i++){
            pid_t p=fork();
            if(p<0){ perror("fork"); return 1; }
            if(p==0){ // child
                size_t start=i*base + (i<rem? i: rem);
                size_t len  = base + (i<rem? 1:0);
                int local_max = (len>0)? arr[start] : INT_MIN;
                for(size_t j=1;j<len;j++) if(arr[start+j]>local_max) local_max=arr[start+j];

                // critical section
                if(sem_wait(sem)==-1){ perror("sem_wait"); _exit(1); }
                if(local_max>*gmax) *gmax=local_max;
                if(sem_post(sem)==-1){ perror("sem_post"); _exit(2); }

                _exit(0);
            }
        }

        // wait for children
        size_t done=0;
        int status=0;
        while(done<nw){
            pid_t c = wait(&status);
            if(c>0) done++;
            else if(errno==EINTR) continue;
            else break;
        }

        long long t1=t_ns(); // end map
        int g=*gmax;
        long long t2=t_ns(); // reduce

        long r=rss_self();

        // verify
        if(verify){
            int m=seq_max(arr,n);
            if(m!=g){ fprintf(stderr,"ERROR global max %d expected %d\n",g,m); return 1; }
        }

        printf("Workers=%zu | GlobalMax=%d | Map=%.3f ms | Reduce=%.3f ms | Total=%.3f ms | MaxRSS=%ld KB\n",
               nw,g,ns_to_ms(t1-t0),ns_to_ms(t2-t1),ns_to_ms(t2-t0),r);
    }

    munmap(gmax,sizeof(int));
    free(arr);
    sem_close(sem);

    return 0;
}






