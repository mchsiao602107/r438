### Create r438 Project in OMNeT++
1. File -> New -> Project -> OMNeT++ -> OMNeT++ Project.
2. Next -> Next -> Empty project with 'src' and 'simulations' folders -> Finish.

### Reference r438 Project to INET Project
1. Right click r438 -> Properties -> Project References.
2. Check out "inet".

### Reference Header Files Defined in INET Source Folder
1. Right click r438 -> Properties -> OMNeT++ -> Makemake -> src -> Options -> Custom.
2. Add following into "Code fragment to be inserted into Makefile":
    ```bash
    CFLAGS += -I/home/mchsiao/omnetpp-6.0/INET_workspace/inet/src
    ```