
## Feat/OCR images and rename with infered title.

This is great!  New feature, OCR to get the text and name the files with the existing file name but appended with an appropriate title based on text (need to send OCR’d text to Deepseek with prompt “come up with title under a certain number of characters, with no spaces but underscores). Note, this should be a separate process but can run in parallel so as to not interupt the original slide building process

Prompt: "come up with title under a 31 character limit, in camel case" Later on, we'll also add timestamps.

### Getting timestamps
- `<div class="w-bottom-bar-lower w-css-reset">`
- `<div class="w-bottom-bar-middle-inner w-css-reset">`
- `<div class="w-css-reset" data-handle="playbar">`
- `<div class="w-playbar-wrapper w-css-reset w-css-reset-tree">`
- `<div class="w-playbar__time">0:35</div>`

## Feat/live transcript generation
Generate transcript from audio in real time.   Note the time stamps in the file