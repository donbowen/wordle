import streamlit as st
from wordle_util import *

def play_wordle(): 
    
    st.write('Welcome to Wordle for cheaters!')
    
    game_state = st.session_state.get('game_state', None)
    if game_state is None:
        game_state = {'game': Wordle(), 'guesses': []}
        
    guess_mode_ans = st.radio('Guess Mode', ['Only guess possible answers (fast)', 'Hard Mode (slow)', 'Consider any allowable guess (slowest)'], index=0)
    if guess_mode_ans == 'Only guess possible answers (fast)':
        game_state['game'].guess_mode = 'answers_only'
    elif guess_mode_ans == 'Hard Mode (slow)':
        game_state['game'].guess_mode = 'hard'
    else:
        game_state['game'].guess_mode = 'all'

    prev_ans_mode = st.radio('Remove previous answers from pool? (extra-cheaty)', ['No','Yes'], index=0)
    if prev_ans_mode == 'Yes':
        st.write('Note: The prior answers dataset is often outdated')
        st.write('Note: NYT might repeat words')
        st.write("Possible answers before removing prior answers:",len(game_state['game'].remaining_answers))
        game_state['game'].remove_previous_answers()
        st.write("Possible answers after removing prior answers:",len(game_state['game'].remaining_answers))
    '''
    ---
    '''            
    st.write('Guess a 5-letter word and the colors (e.g. "apple, bbbbb"):')
    guess_input = st.text_input('Enter your guess and colors:')
    if st.button('Submit'):
        guess, colors = guess_input.split(', ')         # parse guess
        game_state['game'].guess(guess, colors)         # make the guess
        game_state['guesses'].append((guess, colors))   # track guesses
        info_set = game_state['game'].what_next         # get info about possible guesses
        info_set.index.name = 'Rank'
        
        # outputs
        st.write("Possible answers left:",len(game_state['game'].remaining_answers))
        st.write("Info to help your next guess")
        
        # the info about possible guesses
        top_10_rows = info_set.head(10) # might not include viable answers, so let's ensure we print some:
        top_10_rows_viable_ans_is_1 = info_set[info_set['viable_ans'] == 1].head(10)
        result = pd.concat([top_10_rows, top_10_rows_viable_ans_is_1])
        result = result.drop_duplicates()   
        st.write(result.iloc[:,:3])
        
    if st.button('Reset'):
        game_state = {'game': Wordle(), 'guesses': []}
    st.session_state['game_state'] = game_state

if __name__ == '__main__':
    play_wordle()