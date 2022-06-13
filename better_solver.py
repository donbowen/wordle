import pandas as pd

import warnings
warnings.simplefilter("ignore", UserWarning) # shut up regex match group notice in pandas 

# step 1 - load the data
url = "https://raw.githubusercontent.com/donbowen/wordle/main/wordle.csv"
words = pd.read_csv(url, names=["whole_word"])

# step 2 - create columns holding each letter in the given position
words[["pos1", "pos2", "pos3", "pos4", "pos5"]] = words["whole_word"].str.split(
    "", expand=True
)[[1, 2, 3, 4, 5]]

def filter_with_info(exact='-----',yellow='',black='',df=words):
    '''
    exact   = String with 5 hyphens. replace the corresponding one with 
              a letter when you know it's in that spot (green).
              Example: exact = '--a--' 
    black   = String with letters in black
              Example: include = 'tr' will EXCLUDE words with t or r
    yellow  = list of pairs, each element is ('letter',position) where
              position (1-5) is where the letter isn't      
    df      = Remaining viable words. Either dataframe with columns for 
              whole_word, pos1, ... pos5. Or a LIST of words.

    RETURNS LIST OF WORDS THAT STILL WORK
    '''
    
    if type(df) == list:
        df = pd.DataFrame(remaining,columns=['whole_word'])
        df[["pos1", "pos2", "pos3", "pos4", "pos5"]] = df["whole_word"].str.split(
            "", expand=True
        )[[1, 2, 3, 4, 5]]
    
    if len(black) > 0:
        black = '('+''.join([c + '|' for c in black[:-1]])+black[-1]+')'
        df = df[(~df["whole_word"].str.contains(black))]

    if len(yellow) > 0:
        for (c,spot) in yellow:
            df = df[df["whole_word"].str.contains(c)]
            df = df[df['whole_word'].str[spot-1] != c]

    for i,c in enumerate(exact):
        if c != '-':
            df = df[df["whole_word"].str[i] == c]
    
    return df.whole_word.to_list()

def guess_outcomes_basic(df):
    '''
    
    Parameters
    ----------
    df : DATAFRAME of remaining viable words
        Columns: whole_word, pos1, ... pos5

    Returns
    -------
    DATAFRAME
        With info about how much you'll learn from that guessing a given word.

    '''
    
    def any_hits_criteria(word, df):
        myregex = "(" + "|".join(word) + ")"
        cov1 = df["whole_word"].str.count(myregex) >= 1
        cov2 = df["whole_word"].str.count(myregex) >= 2
        cov3 = df["whole_word"].str.count(myregex) >= 3
        cov4 = df["whole_word"].str.count(myregex) >= 4
        cov5 = df["whole_word"].str.count(myregex) >= 5
        out = pd.Series(
            [cov1.mean(), cov2.mean(), cov3.mean(), cov5.mean(), cov5.mean()],
            index=["cov1+", "cov2+", "cov3+", "cov4+", "cov5+"],
        )
        return out
    
    
    def use_any_hits(df, sortcol=4):
        """
        sortcol : int, 1-5
        """
        return df.merge(
            df["whole_word"].apply(any_hits_criteria, df=df),
            left_index=True,
            right_index=True,
        ).sort_values("cov" + str(sortcol) + "+", ascending=False)
    
    def dumb_exact(word, df):
        """
        how many words in the master list does this word
        have 1 exact position match for? 2? 3? 4? 5?
        """
        newindex=[0,1,2,3,4,5]
        
        out = (
            pd.concat(
                [(df["whole_word"].str[i] == c).astype(int) for i, c in enumerate(word)],
                axis=1,
            )
            .sum(axis=1)
            .value_counts()
            .reindex(index=newindex,fill_value=0)[1:]
            .fillna(0)
        )
        out.index = ['exact1+','exact2+','exact3+','exact4+','exact5+']
    
        return out
    
    def use_exact(df, sortcol=4):
        """
        sortcol : int, 1-5
        """
        return df.merge(
            df["whole_word"].apply(dumb_exact, df=df),
            left_index=True,
            right_index=True,
        ).sort_values("exact" + str(sortcol) + "+", ascending=False)
    
    return (
        pd
        .merge(use_exact(df, 3), use_any_hits(df, 3), on="whole_word")
        .filter(regex="(whole|exact|cov)")
        .drop(labels=['exact1+','exact2+','cov1+','cov2+'],axis=1)
    )    

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
        
        # guess_set_dict[guess] = set()
        
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
            pair_info_set = (black,green,yellow)
            
            # add info set to tracking objects         
            
            guess_set_count[(guess,pair_info_set)] += 1
                  

    # output the info we want (some annoying formatting to handle)
    
    outdf          = pd.DataFrame.from_dict(guess_set_count,orient='index',columns=['remaining_options'])
    outdf.index    = pd.MultiIndex.from_tuples(outdf.index,names=['guess','info_set'])
    outdf          = (outdf.reset_index()    
                      .groupby(['guess','remaining_options'],as_index=False)
                      .agg(count=('remaining_options',sum)) 
                     )
    
    # compute avg guess remaining
    
    means = (outdf
             .groupby(['guess'],as_index=False)
             .apply(lambda x: sum(x['count']*x['remaining_options'])/sum(x['count']))
             )
    means.columns = ['guess','avg_remaining']

    # tabluate # time you'll have certain number left
    
    counts = (outdf
              .set_index(['guess','remaining_options'])
              .unstack(fill_value=0)
              )
    counts.columns = [str(c[1])+'_left' for c in counts.columns]
    
    # combine those 
    
    output = means.merge(counts,left_on='guess',right_index=True).sort_values('avg_remaining').reset_index(drop=True)
    
    # shorten output (10+ guess left get collapsed into one col)
    
    if len(output.columns) > 12:
        
        output = pd.concat([output.iloc[:,:11],
                            output.iloc[:,11:].sum(axis=1).to_frame('10+_left')],
                           axis=1)
    
    # combine with info from guess_outcomes_basic
    
    return output.merge(
                        guess_outcomes_basic(output.rename(columns={'guess':'whole_word'})
                                       )
                        .rename(columns={'whole_word':'guess'})
        )
    
def cheat(green='',yellow=[],black='',df=words):
    '''
    exact   = String with 5 hyphens. replace the corresponding one with 
              a letter when you know it's in that spot (green).
              Example: exact = '--a--' 
              Example: '' (means no greens yet)
              Example: '-----' (means no greens yet)
              
    yellow  = list of pairs, each element is ('letter',position) where
              position (1-5) is where the letter isn't      
              Example: [] (means no yellow yet)
              
    black   = String with letters in black
              Example: include = 'tr' will EXCLUDE words with t or r
              Example: '' (means no blacks yet)
              
    df      = Remaining viable words. 
              Can be a list of words or a dataframe with columns for 
              [whole_word, pos1, ... pos5]
    '''
    return guess_outcomes(filter_with_info(green,yellow,black,df))

info_set = cheat('--ink',[],'st')

    
