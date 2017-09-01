# Docker Deployment for OpenWPM

OpenWPM can be run in a Docker container. This is similar to running OpenWPM in a virtual machine, only with less overhead.

## Building the Docker Container

__Step 1:__ install Docker on your system. Most Linux distributions have Docker in their repositories. It can also be installed from [docker.com](https://www.docker.com/). For Ubuntu 16 you can use: ```sudo apt-get install docker.io```

You can test the installation with: ```sudo docker run hello-world```

_Note,_ in order to run Docker without root privileges, add your user to the ```docker``` group (```sudo usermod -a -G docker $USER```). You will have to logout-login for the change to take effect, and possibly also restart the Docker service.


__Step 2:__ for the build, clone this source directory, then from a terminal  within it run the following:


    docker build -t openwpm .

After a few minutes, the container is ready to use.

## Running Measurements from inside the Container

You can run demo measurements from inside the container, as follows:

    docker run -v $PWD/volume:/home/user/  -it openwpm python /home/user/demo-docker.py

This command uses _bind-mounts_ to share scripts and output between the container and host, as explained below (note the paths in the command assume it's being run from the build directory):

- ```run``` starts the ```openwpm``` container and executes the ```python /home/user/demo-docker.py``` command.

- ```-v``` binds a directory on the host (```$PWD/volume```) to a directory in the container (```/home/user```). Binding allows passing the crawl script (```demo-docker.py```) to the container, and makes the script's output to be saved on the host (```volume/Desktop```).

- The ```-it``` option states the command is to be run interactively (use ```-d``` for detached mode).

Notes regarding the demo script:

- At the top of the script, we have added ```import sys``` and ```sys.path.insert(0, '/opt/OpenWPM')```, so the import statements work correctly, as OpenWPM is installed in ```/opt```.

- The script runs headless crawls. If you'd like to show the Firefox windows, you must add additional options  ```-e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix``` so the container can access X-windows.

- Finally, if you intend to run OpenVPN in your crawl scripts, use the ```--privileged``` option.
