import pandas as pd
from collections import defaultdict
import re
import warnings
warnings.simplefilter("ignore", UserWarning) # shut up regex match group notice in pandas 

def order_front(df, to_front):
   '''
   Moves columns in to_front to left of df.
   '''
   cols = list(df.columns)
   for c in to_front:
       cols.pop(cols.index(c))
   cols = to_front + cols
   return df[cols]
       
def determine_wordle_color_response(guess,answer):

    colors = ''
    green = ''.join([guess[i] if guess[i] == answer[i] else '-' for i in range(5)])
    yellow = ()
    
    for idx,let in enumerate(guess):
        supply_tot = answer.count(let)
        supply_left = supply_tot - green.count(let) - len([i for (i, j) in yellow if i==let])
        if let not in answer:
            colors += 'b'
        elif let == answer[idx]:
            colors += 'g'
        else:
            if supply_left > 0:
                colors += 'y'                       
                new_yellow = (let,idx+1)
                yellow += (new_yellow,)
            else:
                colors += 'b'
    
    return colors

class Wordle:
    '''
    A wordle game. Key methods:
    
    .words               list of remaining words
    
    .guess(guess,colors) To tell it what you guessed and the colors you got. 
                         It updates the list of remaining words and produces
                         info about what guesses you can make next. By default,
                         
                         (1) it acts like "hard mode" in the game - only valid 
                         answers satisfying current info are considered for 
                         the next guess
                         
                         (2) it only uses the dictionary of answer words, 
                         ignoring the many real (but obscure) words Wordle 
                         considers a valid guess but aren't in the list of 
                         possible answers

    .what_next           .guess() produces this DF with stats about what 
                         you'll learn from guessing any of the remaining words 

    .golf_score          How far are your guesses from the "optimal"? Here,
                         "optimal" is the guess in .what_next with the lowest 
                         value of avg_remaining.
                         
                         For a single guess, your score is the avg_remaining  
                         of that word minus the avg_remaining of the best 
                         word. So, lower is better, like in golf!
                         
                         The total score is just the sum of your scores for 
                         each guess.
                         
                         It only evaluates you based on your guesses after the
                         first one. This is so you can choose randomly choose
                         a start word for variety without being penalized, and
                         then it starts evaluating your skill.
                         
                         Btw, some info about the best start word:
                             
        guess  avg_remaining  P(1_left)  P(2_left)  P(Green_3+)  P(GorY_3+)
        ---------------------------------------------------------------------
        raise          61.00       1.21       1.04         0.91       20.30
        arise          63.73       1.12       0.43         1.86       20.30
        stare          71.29       0.99       0.86         2.89       22.25
        slate          71.57       1.25       1.73         2.68       18.88
        alert          71.60       1.08       1.12         0.99       21.47
        crate          72.90       1.30       1.73         2.20       19.05
        share          85.47       0.78       1.38         3.15       17.15
        shine         120.24       1.21       1.47         2.68       10.06

    .guess_mode         'answers_only' means we only consider remaining answers 
                        for guesses. 'hard' means we can guess all viable words
                        that aren't eliminated by our info. 'all' means we can
                        guess using any possible guess. The latter two are slower.
                        'all' should trim the remaining options the most.

    ---
    
    USAGE:
        
    To play a game
    
        game = Wordle()
        game.hard_mode = True        # true by default, quicker
        game.guess('super','gbbyb')  # put your guess and the colors you got 
        info_set = game.what_next    # look for a guess by examining info_set
        game.guess(...)              # and make it
        info_set = game.what_next    # look for a guess by examining info_set
        ...
        game.golf_score              # how are you doing?
    
    To examine your guesses:
                        
    --- 
    
    KNOWN ISSUES: 
                            
    IGNORE: The acceptable guess list in the actual game is larger than the 
    acceptable answer list. Sometimes using a weird word that can't be the  
    answer could filter the remaining guesses better. I won't implement this,  
    but it is easy: self.all_words = (DL it)
    '''
    
    def __init__(self):
        # self.remaining_answers will be the list of remaining possible answers         
        # ~2k words, all common words
        self.remaining_answers = pd.read_csv("https://raw.githubusercontent.com/donbowen/wordle/main/wordle.csv", 
                                 names=["whole_word"]).whole_word.to_list()
        
        # self.guess_options_all is all viable answers at the start of the game
        # 12k words, including some obscure ones
        self.guess_options_all = pd.read_csv("https://gist.githubusercontent.com/prichey/95db6bdef37482ba3f6eb7b4dec99101/raw/1b07e3564810daa12277d828c0642b71359fee67/wordle-words.txt", 
                                 names=["whole_word"]).whole_word.to_list()
        
        # self.guess_options_hardmode removes guesses we know to be impossible based on info set
        self.guess_options_hardmode = self.guess_options_all.copy()
        self.black = ''
        self.green = '-----'
        self.yellow = []
        self.golf_score = 0 
        self.what_next = None
        self.guess_mode = 'answers_only'
             
    def remove_previous_answers(self):
        previous_answers = [w.lower() for w in pd.read_csv("https://eagerterrier.github.io/previous-wordle-words/chronological.txt", 
                                 names=["whole_word"]).whole_word.to_list()]        
        print(len(previous_answers))
        self.remaining_answers = [w for w in self.remaining_answers if w not in previous_answers]
                                     
    def guess_outcomes(self):
        '''
        Outputs a dataset. Treats all remaining words as equally likely to be ans. 
        
        For each possible guess, show the average number of words remaining after 
        the info is revealed. Tabulates how many possible words.
        
        Example:
            
                      count   1  2  3  4  5  6
            guess                             
            tepid  1.421053  11  8  0  0  0  0
            deity  1.526316  12  4  3  0  0  0
            edict  1.526316  12  4  3  0  0  0    
            ...
            
        If you guess tepid, for 11 of the possible answer words, tepid will fully
        reveal the answer. For 8 other possible answer words, the info you 
        get will reduce the possible set to 2 words. The avg number of words after 
        the guess is 2.    
        
        ---
        
        Known issues:
            
            Is the answer is the word, the number of remaining options is 1. 
            But in the use of the function, we want to know "how many more guesses
            after this one". So 1_left should be minus 1 in the "counts" object.
        
        '''
        
        if self.guess_mode == 'answers_only':
            guess_list = self.remaining_answers
        elif self.guess_mode == 'hard' : 
            guess_list=self.guess_options_hardmode 
        else:
            guess_list=self.guess_options_all
    
        # # keep a count of # times that guess yields each of possible sets 
        # # note: sum this count for a given guess = # of possible words remaining
    
        # guess_set_count    = defaultdict(int) 
    
        # # get possible info sets from all potential next guesses
        # # if we were going to simulate millions of games and guesses, 
        # # could pre-compile a {(guess,answer):info_set} dictionary and just 
        # # do look ups here. but not worth it.
    
        # for guess in guess_list:    
                    
        #     for answer in self.remaining_answers:
                    
        #         # get info set this guess would get for the given answer
                
        #         black = ''.join([e for e in set(guess) if e not in set(answer)])
        #         black = ''.join(sorted(black)) # only membership matters, sort so 'ab' and 'ba' are equiv
        #         green = ''.join([guess[i] if guess[i] == answer[i] else '-' for i in range(5)])
        #         yellow = ()
        #         for idx,let in enumerate(guess):
        #             # acct for cases when you guess a letter multiple times
        #             # wordle will asgn yellow to first instance of it left to 
        #             # right, such that yellow+green<=the # of times it is in 
        #             # the answer
        #             supply_tot = answer.count(let)
        #             supply_left = supply_tot - green.count(let) - len([i for (i, j) in yellow if i==let])
        #             if let in answer and not let == answer[idx] and supply_left > 0:
        #                 new_yellow = (let,idx+1)
        #                 yellow += (new_yellow,)
                
        #         # TODO? - this doesn't track count info - when a guess has 
        #         # repeat letters, if guess.count(let)>answer.count(let), that 
        #         # let is in there answer.count(let) times and the wordle colors
        #         # reveal that. If <=, all have colors and we learn the letter
        #         # is in there at least guess.count(let) times. 
                                
        #         # add info set to tracking objects         
                
        #         guess_set_count[(guess,(black,green,yellow))] += 1
                      
        def compute_info_set_vectorized(guesses, answers):
            black = []
            green = []
            yellow = []

            for guess in guesses:
                for ans in answers:
                    black.append(''.join(sorted(set(guess) - set(ans))))
                    green.append(''.join([g if g == a else '-' for g, a in zip(guess, ans)]))
                    yellow_ans = []
                    for idx, let in enumerate(guess):
                        if let in ans and guess[idx] != ans[idx]:
                            yellow_ans.append((let, idx+1))
                    yellow.append(tuple(yellow_ans))
                    
            return black, green, yellow

        def build_dictionary_vectorized(guess_list, remaining_answers):
            guess_set_count = defaultdict(int)

            black, green, yellow = compute_info_set_vectorized(guess_list, remaining_answers)
            print(len(yellow))
            for i, guess in enumerate(guess_list):
                for j, answer in enumerate(remaining_answers):
                    info_set = (black[i*len(remaining_answers)+j], green[i*len(remaining_answers)+j], yellow[i*len(remaining_answers)+j])
                    guess_set_count[(guess, info_set)] += 1

            return guess_set_count
    
        guess_set_count = build_dictionary_vectorized(guess_list, self.remaining_answers)
    
        # output the info we want (some annoying formatting to handle)
        
        guess_set_df          = pd.DataFrame.from_dict(guess_set_count,orient='index',
                                                columns=['remaining_options'])
        guess_set_df.index    = pd.MultiIndex.from_tuples(guess_set_df.index,
                                                   names=['guess','info_set'])
            
        # for outputs based on the number of remaining options, we need to agg 
        # to obs levels guess+remaining
        
        outdf          = (guess_set_df.reset_index()    
                          .groupby(['guess','remaining_options'],as_index=False)
                          .agg(count=('remaining_options',sum)) 
                         )
            
        # compute avg possibilities remaining after a given guess
        
        means = (outdf
                 .groupby(['guess'],as_index=False)
                 .apply(lambda x: sum(x['count']*x['remaining_options'])/sum(x['count']))
                 )
        means.columns = ['guess','avg_remaining']
    
        # tabluate # time you'll have certain number of answers left after a given guess
        
        counts = (outdf
                  .set_index(['guess','remaining_options'])
                  .unstack(fill_value=0)
                  )
        counts.columns = [str(c[1])+'_left' for c in counts.columns]
        
        # combine those dataframes 
        
        output = (means
                  .merge(counts,left_on='guess',right_index=True)
                  .sort_values('avg_remaining')
                  .reset_index(drop=True)
                  )
        
        # shorten output (10+ guess left get collapsed into one col)
        
        if len(output.columns) > 12:
            
            output = pd.concat([output.iloc[:,:11],
                                output.iloc[:,11:].sum(axis=1).to_frame('10+_left')],
                               axis=1)
    
        # get a different set of info: how many guesses have certain amounts of info?
        
        guess_aggs = guess_set_df.reset_index()
        guess_aggs[['black', 'green','yellow']] = pd.DataFrame(guess_aggs['info_set'].tolist(), 
                                                index=guess_aggs.index)
        guess_aggs['NGreen'] = guess_aggs['green'].apply(lambda x: 5-x.count('-'))
        guess_aggs['NYellow'] = guess_aggs['yellow'].apply(lambda x: len(x))
        
        def my_agg(x):
            names = {
                'Green_3+': x.query('NGreen >= 3')['remaining_options'].sum(),
                'Green_4+': x.query('NGreen >= 4')['remaining_options'].sum(),
                'GorY_3+' : x.query('NGreen + NYellow >= 3')['remaining_options'].sum(),
                'GorY_4+' : x.query('NGreen + NYellow >= 4')['remaining_options'].sum(),
                'GorY_5'  : x.query('NGreen + NYellow >= 5')['remaining_options'].sum()}
    
            return pd.Series(names)
        
        guess_aggs = guess_aggs.groupby('guess',as_index=False).apply(my_agg)    
    
        # combine that with the output data
        
        output = output.merge(guess_aggs)
        output.iloc[:,-5] = output.iloc[:,-5]/len(output)
        
        output['viable_ans'] = output['guess'].isin(self.remaining_answers)
        output = order_front(output, ['guess','viable_ans'])
        minimum = output['avg_remaining'].min()
        output = output.query('guess in @self.remaining_answers | avg_remaining <= @minimum + 0.5')
        
        return output
    
    def guess(self,guess,colors):
        assert len(guess) == 5,  "Guess must be 5 letters"
        assert len(colors) == 5, "Colors of guess must be 5 letters"
        assert set(colors) <= {'y','b','g'}, 'Colors can only be "y" (yellow), "g" (green), or "b" (black)'  
        
        if self.what_next is not None: # if true, this isn't your first guess
            self.golf_score += self.what_next.set_index('guess').loc[guess,'avg_remaining'] - self.what_next.avg_remaining.min()
            
        def replace_let(s,let,index):
            'Returns string "s" with letter "let" in index position'
            return s[:index] + let + s[index + 1:]
        
        # when a guess has repeat letters, we need to use the info correctly,
        # so lets track the colors assoc with a letter
        
        let_colors_dict = defaultdict(list) 
        for l,c in zip(guess,colors):
            let_colors_dict[l].append(c)
        
        # now update info space for black, green, yellow
    
        for spot, (l, c) in enumerate(zip(guess,colors)):     
            # if you guess "missy" and answer only has one "s", wordle will 
            # say the second "s" is black. ignore that (bc in this code, black
            # means its not in the word at all)
            if c == 'b' and not ('y' in let_colors_dict[l] or 'g' in let_colors_dict[l]):
                self.black += l
            elif c == 'g':
                self.green = replace_let(self.green,l,spot)     
            elif c == 'y':
                self.yellow.append((l,spot)) 
                                    
        # use that to filter remaining options 
        
        self.remaining_answers = [w for w in self.remaining_answers if
                      not any(b in w for b in self.black) 
                      and re.match(self.green.replace('-', '.'),w)
                      and all(c in w and w[spot] != c for (c,spot) in self.yellow)
                     ]   
        
        # if the guess has repeat letters, use that info
        
        for let,colors in let_colors_dict.items():
            if len(colors) > 1:
                if 'b' in colors:
                    non_b = len([c for c in colors if c != 'b'])
                    self.remaining_answers = [w for w in self.remaining_answers if w.count(let) == non_b]                    
                else:
                    self.remaining_answers = [w for w in self.remaining_answers if w.count(let) >= len(colors)]
        
        # repeat that for guess_options_hardmode
        self.guess_options_hardmode  = [w for w in self.guess_options_hardmode  if
                      not any(b in w for b in self.black) 
                      and re.match(self.green.replace('-', '.'),w)
                      and all(c in w and w[spot] != c for (c,spot) in self.yellow)
                     ]   
        for let,colors in let_colors_dict.items():
            if len(colors) > 1:
                if 'b' in colors:
                    non_b = len([c for c in colors if c != 'b'])
                    self.guess_options_hardmode = [w for w in self.guess_options_hardmode if w.count(let) == non_b]                    
                else:
                    self.guess_options_hardmode = [w for w in self.guess_options_hardmode if w.count(let) >= len(colors)]
        
        # now, what should we guess next?
        
        assert len(self.remaining_answers) > 0, "No words are possible because colors in your guesses give conflicting info."
        self.what_next = self.guess_outcomes()
                
def game_score(answer,guesses):
    '''
    How did your guesses do compared to one definition of optimal?
    
    This function examines your guesses, ignoring the first guess; have fun 
    with the start word, but then use your skill!
    
    Example:
        
        game_score('primo',['radon','sport','power'])
    '''
    game = Wordle() 
    for guess in guesses:
        colors = determine_wordle_color_response(guess,answer)
        game.guess(guess,colors)
    return game.golf_score 
        
# Let's play!

if __name__ == "__main__":
    game = Wordle()  
    print(game.guess_outcomes())  # starting words, ranked

    # game.guess('smile','bbbbb')
    # info_set = game.what_next
    # print(info_set)
    # info_set.set_index('guess').loc[['pouty','proud','grant','pound','hound'],'avg_remaining']
    # game.guess('grant','byyyb')
    # print(game.golf_score)

# game_score('apron',['smile','pouty','whoop','apron'])         # 7.15 - Don
# game_score('apron',['smile','proud','apron'])                 # 5.44 - Nick
# game_score('apron',['smile','grant','apron'])                 # 1.23 - Mustafa
# game_score('apron',['smile','pound','apron'])                 # 6.91 - Mary
# game_score('apron',['smile','hound','grown','baron','apron']) # 5.11 - Steph