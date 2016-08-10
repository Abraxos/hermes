<h1> Hermes-Native-UI</h1>
<p>The UI Component for the Hermes Messenger application. https://github.com/Abraxos/hermes. Currently a work in progess.</p>

<h2> Kivy Installation in Virtual Env (directly copied from their site)</h2>


<h3> Install necessary system packages </h3>

```
sudo apt-get install -y \
    python-pip \
    build-essential \
    git \
    python \
    python-dev \
    ffmpeg \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libswscale-dev \
    libavformat-dev \
    libavcodec-dev \
    zlib1g-dev
```
<p> <i> Note: Depending on your Linux version, you may receive error messages related to the “ffmpeg” package. In this scenario, use “libav-tools ” in place of “ffmpeg ” (above), or use a PPA (as shown below):</i></p>
```
- sudo add-apt-repository ppa:mc3man/trusty-media
- sudo apt-get update
- sudo apt-get install ffmpeg
```
<h3>Installation</h3>
<p>Make sure Pip, Virtualenv and Setuptools are updated</p>
```
sudo pip install --upgrade pip virtualenv setuptools
```
<p>Create a virtualenv</p>
```
virtualenv --no-site-packages kivyinstall
```
<p>Enter the virtualenv</p>
```
. kivyinstall/bin/activate
```
<p>Use correct Cython version here</p>
```
pip install Cython==0.23
```
<p>Install stable version of Kivy into the virtualenv</p>
```
pip install kivy
```
<p>For the development version of Kivy, use the following command instead</p>
```
pip install git+https://github.com/kivy/kivy.git@master
```
<h3>Running the Messanger</h3>
<p>Put messanger.kv and messanger.py in the same directory and run the line below whilst working on the virtualenv kivyinstall:</p>

```
python  messanger.py
```
