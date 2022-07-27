INET Simulation
===

### Outline
- [Workspace Structure](#workspace-structure)
- [Project Setup](#project-setup)
    - [Create r438 Project in OMNeT++](#create-r438-project-in-omnet)
    - [Reference r438 Project to INET Project](#reference-r438-project-to-inet-project)
    - [Reference Header Files Defined in INET Source Folder](#reference-header-files-defined-in-inet-source-folder)

### Workspace Structure
```bash
.
├── inet               
└── r438
    ├── src
    └── simulations
    └── util            # Contain Python file to generate .ini file
    └── rust            # Contain modified main.rs                  
```

### Project Setup

### Create r438 Project in OMNeT++
- File&rarr;New Project&rarr;OMNeT++&rarr;OMNeT++ Project&rarr;Next&rarr;Next&rarr;Empty project with 'src' and 'simulations' folders&rarr;Finish

### Reference r438 Project to INET Project
- Right click r438&rarr;Properties&rarr;Project References&rarr;Check out inet

### Reference Header Files Defined in INET Source Folder
- Right click r438&rarr;Properties&rarr;OMNeT++&rarr;Makemake&rarr;src&rarr;Options&rarr;Custom&rarr;Add following into "Code fragment to be inserted into Makefile"
```bash
CFLAGS += -I/home/mchsiao/omnetpp-6.0/INET_workspace/inet/src
```