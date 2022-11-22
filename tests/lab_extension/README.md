# Setting up the Jupyter-lab extension tests

To run the pyquibbler lab-extension tests, you'll need to install `chromedriver`, 
which allows selenium to run and control a browser. 

To install `chromedriver` and add it to your path:

#### 1. Download and unzip chromedriver 
Go to https://chromedriver.chromium.org/downloads, and download the chromedriver corresponding to your chrome version and operating system.
You can get your Chrome version by choosing "About Google Chrome" in the Chrome menu (e.g., 102.0.x).
After clicking on the correct version, you'll be able to choose your operating system. After downloading, you will
need to click the downloaded archive to unzip it. 

#### 2. Place the chromedriver in your path 
After downloading and unzipping chromedriver, go to your terminal and run `echo $PATH` (or `path` on Windows). 
This will show you a set of locations separated by a colon where executable files are expected to be found.
You need to place your downloaded chromedriver in one of them (if `/usr/local/bin` is in your PATH, we recommend
placing it there).

For example, to place it in the /usr/local/bin folder, run 

   `mv ~/Downloads/chromedriver /usr/local/bin/`

#### 3. Make the chromedriver file executable
After placing the chromedriver in your PATH, we need to make it executable. 
To do this, run:

   `chmod 777 /usr/local/bin/chromedriver`

#### 4. Run the tests! 
Go to `tests/lab_extension` and run `pytest`. 


### Troubleshooting 

If tests fail, try:
1. when running the tests, make sure the chrome selenium opens is visible to you 
(there are issues with jupyter when it's not, as it doesn't load).

2. restart pycharm

3. If getting _“chromedriver” cannot be opened because the developer cannot be verified_, 
   try running:
   
      ```xattr -d com.apple.quarantine /usr/local/bin/chromedriver```
