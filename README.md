# What is this?

A wordle cheat. Especially the app.py streamlit app.

[You can see this app in action here!]())

## How to - streamlit

If you want to get this app working on your computer so you can use it, play around with it, or modify it, you need:
1. A working python / Anaconda installation
1. Git 

The, open a terminal and run these commands one at a time:

```sh
# download files (you can do this via github desktop too)
cd <path to some parent folder> # make sure the cd isn't a repo or inside a repo!
git clone git@github.com:donbowen/wordle_streamlit.git

# move the terminal to the new folder
cd <path to some parent folder containing the downloaded repo> 
cd wordle_streamlit

# set up the packages you need for this app to work
conda env create -f environment.yml
conda activate streamlit-env

# start the app in a browser window
streamlit run app.py

# open any IDE you want to modify app 
spyder  # and when you save the file, the app website will update
```

When you are ready to deploy the site on the web, 
1. Save the repo to your own account.
1. Go to streamlit's website, sign up, and deploy it by giving it the URL to your repo.
1. Wait a short time... and voila!

### Notes

While it seems duplicative to have a `requirements.txt` and a  `environment.yml`, the former is needed by Streamlit and the latter makes setting up a conda environment quickly easy. 



## Non-streamlit stuff: Some silly wordle analyis

- `wordle.ipynb` is some exploratory code that produced this analysis
- `wordle.py` makes it easy to see available guess options and what you'll learn from guessing them. Doing so is cheating, obviously, but it's useful to learn about how good your guesses are. There is a nice way to evaluate your guesses too.
- `wordle.csv` is the list of possible answers to the game

### First word choice

If your decision rule is
- Highest likelihood of
  - Getting 1+ matches (not neccesarily exact spot): ARISE
  - Getting 2+ matches (not neccesarily exact spot): AROSE
  - Getting 3+ matches (not neccesarily exact spot): ALERT
  - Getting 1+ exact position matches: SLATE
  - Getting 2+ exact position matches: SHINE
  - Getting 3+ or 4+ exact position matches: SHARE

### Letter frequency

| Letter | In word list 	| In pos1 	| In pos2 	| In pos3 	| In pos4 	| In pos5 |
|---|---|---|---|---|---|---|
e 	| 1233 	 		| 72 	| 242 	| 177 	| 318 	| 424
a 	| 979 	 		| 141 	| 304 	| 307 	| 163 	| 64
r 	| 899 	 		| 105 	| 267 	| 163 	| 152 	| 212
o 	| 754 	 		| 41 	| 279 	| 244 	| 132 	| 58
t 	| 729 	 		| 149 	| 77 		| 111 	| 139 	| 253
l 	| 719 	 		| 88 	| 201 	| 112 	| 162 	| 156
i 	| 671 	 		| 34 	| 202 	| 266 	| 158 	| 11
s 	| 669 	 		| 366 	| 16 		| 80 		| 171 	| 36
n 	| 575 	 		| 37 	| 87 		| 139 	| 182 	| 130
c 	| 477 	 		| 198 	| 40 		| 56 		| 152 	| 31
u 	| 467 	 		| 33 	| 186 	| 165 	| 82 	| 1
y 	| 425 	 		| 6 	| 23 		| 29 		| 3 	| 364
d 	| 393 	 		| 111 	| 20 		| 75 		| 69 	| 118
h 	| 389 	 		| 69 	| 144 	| 9 		| 28 	| 139
p 	| 367 	 		| 142 	| 61 		| 58 		| 50 	| 56
m 	| 316 	 		| 107 	| 38 		| 61 		| 68 	| 42
g 	| 311 	 		| 115 	| 12 		| 67 		| 76 	| 41
b 	| 281 	 		| 173 	| 16 		| 57 		| 24 	| 11
f 	| 230 	 		| 136 	| 8 		| 25 		| 35 	| 26
k 	| 210 	 		| 20 	| 10 		| 12 		| 55 	| 113
w 	| 195 	 		| 83 	| 44 		| 26 		| 25 	| 17
v 	| 153 	 		| 43 	| 15 		| 49 		| 46 	| 0
z 	| 40 	 		| 3 	| 2 		| 11 		| 20 	| 4
x 	| 37 	 		| 0 	| 14 		| 12 		| 3 	| 8
q 	| 29 	 		| 23 	| 5 		| 1 		| 0 	| 0
j 	| 27 	 		| 20 	| 2 		| 3 		| 2 	| 0


