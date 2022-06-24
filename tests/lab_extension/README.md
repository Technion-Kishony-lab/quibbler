
# Lab extension tests setup

To run the tests, you'll need the chromedriver (which allows selenium to run a browser it's in control of)
and then add it to your path.

To do this:

1. Go to https://chromedriver.chromium.org/downloads, and download the chromedriver corresponding to your chrome version and operating system.
You can check your chrome version by clicking on chrome and going to "About Google Chrome".
You should see 102.0.x. After clicking on the correct version, you'll be able to choose your operating system.
2. Unzip the chromedriver (by clicking on the archive)
3. After downloading your chromedriver, go to your terminal. Run `echo $PATH`. This will show you a set of locations seperated by a colon where executable files are expected to be found.
You need to place your chromedriver in one of them. If `/usr/local/bin` is in your PATH, the experts at Quibbler recommend placing it there. 
To place it in this location, run `mv ~/Downloads/chromedriver /usr/local/bin/`
4. After placing the chromedriver in your PATH, we need to make it executable. To do this, run
`chmod 777 /usr/local/bin/chromedriver`
5. If you haven't already, go to pyquibbler's directory and run 
`pip install -e .[dev]`
6. Run the tests! Go to `tests/lab_extension` and run `pytest`. If tests fail, you can try two things:
   1. when running the tests, make sure the chrome selenium opens is visible to you (there are issues with jupyter when it's not, as it doesn't load)
   2. restart pycharm
   