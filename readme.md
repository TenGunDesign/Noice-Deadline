# Noice Deadline

A Deadline render manager plugin to support the Arnold renderer's denoiser, Noice. 

## Installation
Download the latest [release](https://github.com/TenGunDesign/Noice-Deadline/releases/latest/download/NoiceDeadline.zip). Copy the contents of `plugins` and `submission` into the corresponding subdirectories of your Deadline repository's `custom` directory. The submission GUI is now available in Deadline's `Submit` menu. As super user, you will want to move the menu item to the `Processing` submenu using `Tools>Configure Script Menus`. We also recommend using the icon from `plugins/Arnold` in your repository.

## Usage
Open the submission GUI from Deadline Monitor. You will find the customary settings under Job Description and Job Options. Under Noice Options, use Input Pattern to browse for an image from the sequence you wish to denoise. The frame list and output pattern will populate automatically with the conventions of the Maya Noice GUI. You can learn more about the remaining settings from the [official documentation](https://docs.arnoldrenderer.com/display/A5AFMUG/Arnold+Denoiser).

## Development
Use the `deploy.py` script to copy source files into your Deadline repository. To test functions without deploying, use `$DEADLINE_PATH/deadlinecommand -ExecuteScriptNoGui` in place of `python` to run your scripts. This will make Deadline-related imports available. 
