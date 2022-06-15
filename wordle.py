import pandas as pd
import warnings
warnings.simplefilter("ignore", UserWarning) # shut up regex match group notice in pandas 

def guess_outcomes(list_of_remaining_words):
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
    
    '''

    from collections import defaultdict
    import pandas as pd

    # keep a count of # times that guess yields each of possible sets 
    # note: sum this count for a given guess = # of possible words remaining

    guess_set_count    = defaultdict(int) 

    # iterate over guess/answer pairs: O(N^2), (unavoidable? ... but fast)

    for guess in list_of_remaining_words:    
                
        for answer in list_of_remaining_words:

            # get info set this guess would get for the given answer
            
            black = ''.join([e for e in set(guess) if e not in set(answer)])
            black = ''.join(sorted(black)) # only membership matters, sort so 'ab' and 'ba' are equiv
            green = ''.join([guess[i] if guess[i] == answer[i] else '-' for i in range(5)])
            yellow = ()
            for idx,let in enumerate(guess):
                if let in answer and not let == answer[idx]:
                    new_yellow = (let,idx+1)
                    yellow += (new_yellow,)
            
            # add info set to tracking objects         
            
            guess_set_count[(guess,(black,green,yellow))] += 1
                  

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
    return output
        
class Wordle:
    '''
    A wordle game. 
    
    .words               list of remaining words
    
    .guess(guess,colors) to tell it what you guessed and the colors you got, 
                         and it updates the list of remaining words   
                         
    .what_next           a dataframe with stats about what you'll learn 
                         from guessing any of the remaining words 
               
    --- 
    Known issue: If you guess a word with repeat letters, you will learn that 
    it is in the word 0, 1, or 2+ times. That info is not used properly.
            
        - Suboptimal solver: If that letter is in it only 1 time, info not used
        if you just get back 1 yellow.
        
        - Suboptimal solver: If that letter is in it 2+ time, info not used if
        you get back 1 or 2 yellow.
    
    '''
    
    def __init__(self):
        self.black = ''
        self.green = '-----'
        self.yellow = []
        self.words = pd.read_csv("https://raw.githubusercontent.com/donbowen/wordle/main/wordle.csv", 
                                 names=["whole_word"]).whole_word.to_list()
               
    def filter_with_info(self):
        '''
        Returns list of words that still work given current info.
        
        NOTE: This does NOT include a check for the cases when we know a given
        letter is in the word twice.
        '''
        import re
        return [w for w in self.words if
                not any(b in w for b in self.black) 
                and re.match(self.green.replace('-', '.'),w)
                and all(c in w and w[spot] != c for (c,spot) in self.yellow)
                ]
                    
    def guess(self,guess,colors):
        assert len(guess) == 5,  "Guess must be 5 letters"
        assert len(colors) == 5, "Colors of guess must be 5 letters"
        assert set(colors) <= {'y','b','g'}, 'Colors can only be "y" (yellow), "g" (green), or "b" (black)'   
        
        def replace_let(s,let,index):
            'Returns string "s" with letter "let" in index position'
            return s[:index] + let + s[index + 1:]

        # update info space
                
        for spot, (l, c) in enumerate(zip(guess,colors)):
            if c == 'b':
                self.black += l
            elif c == 'g':
                self.green = replace_let(self.green,l,spot)     
            elif c == 'y':
                self.yellow.append((l,spot)) 
        
        # if we guess a word with duplicate letters, 
        # one of them might be black even though the other is green or yellow. 
        # remove that letter from the set of black letters
        # this must be done before the filter_with_info function 
        
        from collections import Counter
        guess_counts = Counter(guess)
        for l, count in guess_counts.items():
            if count > 1:
                l_colors = [c for let,c in zip(guess,colors) if let == l]
                if "g" in l_colors or "y" in l_colors:
                    self.black = self.black.replace(l, "")
                            
        # filter to remaining options
        self.words = self.filter_with_info()
        
        # todo - use info about amount of letters in word 
        # if count > 1 and b in l_colors, that letter is in there count times minus number of b's
        # if count > 1 and not b in l_colors, that letter is in there at least count times 
        
        # what should we guess?
        assert len(self.words) > 0, "No words are possible because colors in your guesses give conflicting info."
        self.what_next = guess_outcomes(self.words)
        
# Let's play!

game = Wordle()        
game.guess('sissy','bgggg')
info_set = game.what_next      


    
