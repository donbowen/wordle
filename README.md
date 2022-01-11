# Some silly wordle analyis

Sorry: It's poorly commented code. 

## First word choice

If your decision rule is
- Highest likelihood of
  - Getting 1+ matches (not neccesarily exact spot): ARISE
  - Getting 2+ matches (not neccesarily exact spot): AROSE
  - Getting 3+ matches (not neccesarily exact spot): ALERT
  - Getting 1+ exact position matches: SLATE
  - Getting 2+ exact position matches: SHINE
  - Getting 3+ or 4+ exact position matches: SHARE

## Letter frequency

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


