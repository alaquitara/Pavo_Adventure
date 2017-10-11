import json
import re

import noise_words as noise
import prepositions as prep
import master_words as words

class REGEX_PATTERNS:
    KNOWN_ACTION_AND_ITEM = "recognized_action_and_recognized_item"
    KNOWN_ACTION_AND_ROOM = "recognized_action_and_recognized_room"
    KNOWN_ACTION_AND_FEATURE = "recognized_action_and_recognized_feature"
    NO_MATCH = "no_match"

class WORD_TYPES:
    ACTION = "action"
    EXIT = "exit"
    FEATURE = "feature"
    ITEM = "item"
    ROOM = "room"

class COMMAND_TYPES:
    ACTION_ONLY = "action_only"
    EXIT = "exit"
    EXIT_ONLY = "exit_only"
    FEATURE_ACTION = "feature_action"
    FEATURE_ONLY = "feature_only"
    ITEM_ACTION = "item_action"
    ITEM_ONLY = "item_only"
    OTHER = "other"
    ROOM_ACTION = "room_action"
    ROOM_ONLY = "room_only"

class OUTPUT_FIELDS:
    ACTION = "action"
    DIRECTION = "direction"
    EXIT = "exit"
    FEATURE = "feature"
    GENERAL = "general"
    ITEM = "item"
    NAME = "name"
    OTHER = "other"
    PROCESSED = "processed"
    ROOM = "room"
    TYPE = "type"

# Private functions
# ----------------------------------------------------------------------------
def _preprocess(input_string):
    """
    Makes string lower case and removes any characters other than letters,
    numbers, and a space.

    Returns: A processed string.
    """
    preprocessed_string = input_string.lower()
    # Remove any character that is not a number or letter.
    preprocessed_string = re.sub('[^A-Za-z0-9 ]', '', preprocessed_string)
    return preprocessed_string

def _check_for_exact_match(input_string):
    """
    Checks whether the input_string matches one (and only one) of the
    words recognized by the program directly. If so, the parser
    can bypass all of the other text processing and matching functions
    and go directly to building an output dict.

    Returns: A boolean specifying whether there was an exact match.
    """
    if input_string in words.all_words:
        return True
    return False

def _build_exact_match_output(input_string):
    """
    Where the input_string consists of a single word recognized by the program,
    creates and returns an output dict for that word.

    Returns: A dict containing information about the input. The format of the
             output dict varies depending on the type of the word input.
    """
    #TODO: Add error handling for situation in which word is not actually in dict?
    input_word = input_string
    word_type = words.all_words[input_word]["type"]
    master_word = words.all_words[input_word]["master_word"]
    # All of these dicts will have processed equal True.
    output_dict = {
        OUTPUT_FIELDS.OTHER: {
            OUTPUT_FIELDS.PROCESSED: True
        }
    }
    # Build the rest of the output dict based on the word type of the command.
    if word_type == WORD_TYPES.ACTION:
        output_dict[OUTPUT_FIELDS.TYPE] = COMMAND_TYPES.ACTION_ONLY
        action_dict = {
            OUTPUT_FIELDS.ACTION: master_word
        }
        output_dict[OUTPUT_FIELDS.GENERAL] = action_dict
    if word_type == WORD_TYPES.EXIT:
        output_dict[OUTPUT_FIELDS.TYPE] = COMMAND_TYPES.EXIT_ONLY
        exit_dict = {
            OUTPUT_FIELDS.EXIT: master_word
        }
        output_dict[OUTPUT_FIELDS.EXIT] = exit_dict
    if word_type == WORD_TYPES.FEATURE:
        output_dict[OUTPUT_FIELDS.TYPE] = COMMAND_TYPES.FEATURE_ONLY
        feature_dict = {
            OUTPUT_FIELDS.NAME: master_word
        }
        output_dict[OUTPUT_FIELDS.FEATURE] = feature_dict
    if word_type == WORD_TYPES.ITEM:
        output_dict[OUTPUT_FIELDS.TYPE] = COMMAND_TYPES.ITEM_ONLY
        item_dict = {
            OUTPUT_FIELDS.NAME: master_word
        }
        output_dict[OUTPUT_FIELDS.ITEM] = item_dict
    if word_type == WORD_TYPES.ROOM:
        output_dict[OUTPUT_FIELDS.TYPE] = COMMAND_TYPES.ROOM_ONLY
        room_dict = {
            OUTPUT_FIELDS.ROOM: master_word
        }
        output_dict[OUTPUT_FIELDS.ROOM] = room_dict
    return output_dict

def _remove_noise(input_string):
    """
    Returns a copy of the input string with any words that are on the noise
    words list removed.

    Returns: A string with the noise words removed.
    """
    string = input_string
    noise_words = noise.noise_words
    re_noise_words = '|'.join(word for word in noise_words)
    # Remove the noise words if they are the beginning of the input string and
    # followed by a space, between two spaces, or at the end of the input
    # string and preceeded by a space. That is, if a word is within another
    # word (e.g., 'the' is within 'theater'), do not remove it.
    noise_at_start_of_string = '\A' + re_noise_words + ' '
    string = re.sub(noise_at_start_of_string, '', string, count=1)
    noise_at_end_of_string = ' (' + re_noise_words + ')$'
    string = re.sub(noise_at_end_of_string, '', string, count=1)
    noise_in_middle_of_string = ' (' + re_noise_words + ') '
    string = re.sub(noise_in_middle_of_string, ' ', string)
    # If removing the noise leaves more than one space between words, remove
    # that extra space.
    string = re.sub(' +', ' ', string)
    return string

def _normalize(input_string):
    """
    TODO: Write docs
    """
    return 0

def _generate_full_match_regex_patterns():
    """
    TODO: Write docs

    Returns: A dict of regex patterns and their labels.
    """
    patterns = {}
    # Generate '|'-separated lists of each word type
    action_or = '|'.join(action for action in words.actions)
    item_or = '|'.join(item for item in words.items)
    room_or = '|'.join(room for room in words.rooms)
    # Create list of different patterns that consist entirely of
    # known words.
    patterns[REGEX_PATTERNS.KNOWN_ACTION_AND_ITEM] = \
        '(' + action_or + ') (' + item_or + ')'
    patterns[REGEX_PATTERNS.KNOWN_ACTION_AND_ROOM] = \
        '(' + action_or + ') (' + room_or + ')'
    return patterns

def _match_user_input_pattern(input_string, regex_patterns):
    """
    Determines whether any of the regex patterns specified match the input
    string and outputs a tuple identifying the matching pattern and matching
    words (if any).

    Returns: If a match was found, returns a tuple containing the pattern key,
    which identifies the matching pattern, and a list of the groups that
    matched. If no match was found, returns a ("no_match", []) tuple.
    """
    for pattern_key, pattern in regex_patterns.iteritems():
        match = re.match(pattern, input_string)
        if match:
            return (pattern_key, list(match.groups()))
    return (REGEX_PATTERNS.NO_MATCH, [])

def _generate_output_from_pattern_key(pattern_key, matched_words):
    """
    TODO: Write docs
    """
    output_dict = {}
    if pattern_key == REGEX_PATTERNS.NO_MATCH:
        command_type = COMMAND_TYPES.OTHER
        other_info = {"processed": False}
    else:
        other_info = {"processed": True}
        if pattern_key == REGEX_PATTERNS.KNOWN_ACTION_AND_ITEM:
            # Given the pattern key, we know that the first
            # word matched is an action and the second word matched is an
            # item.
            command_type = COMMAND_TYPES.ITEM_ACTION
            action = matched_words[0]
            item = matched_words[1]
            item_info = {"name": item, "action": action}
            output_dict["item"] = item_info
        elif pattern_key == REGEX_PATTERNS.KNOWN_ACTION_AND_ROOM:
            # Given the pattern key, we know that the first
            # word matched is an action and the second word matched is a room.
            command_type = COMMAND_TYPES.ROOM_ACTION
            action = matched_words[0]
            room = matched_words[1]
            room_info = {"name": room, "action": action}
            output_dict["room"] = room_info
    # Every pattern will have a "type" and "other" key.
    output_dict["type"] = command_type
    output_dict["other"] = other_info
    return output_dict

def _generate_output_for_partial_or_no_match(input_string):
    """
    TODO: Write docs
    """
    # Break input string into individual words.
    input_words = input_string.split()
    # Check if each word is on the master words list.
    recognized_words = {}
    for word in input_words:
        # If a word is on the master words list, add its corresponding
        # master word and type to the recognized words dict.
        if word in words.all_words:
            master_word = words.all_words[word]["master_word"]
            word_type = words.all_words[word]["type"]
            recognized_words[master_word] = word_type
    # Construct an output dict.
    output_dict = {}
    command_type = COMMAND_TYPES.OTHER
    other_info = {"processed": False}
    output_dict["type"] = command_type
    output_dict["other"] = other_info
    if recognized_words:
        output_dict["recognized_words"] = recognized_words
    return output_dict

# Public function
# ----------------------------------------------------------------------------
def parse_command(command):
    """
    TODO: Write docs
    """
    command = _preprocess(command)
    # Exit early if the input string consists of a single, recognized word.
    # In that case, no other processing/matching is necessary.
    if (_check_for_exact_match(command)):
        return _build_exact_match_output(command)
    command = _remove_noise(command)
    # Try matching recognized words with the full user input.
    full_patterns = _generate_full_match_regex_patterns()
    match_info = _match_user_input_pattern(command, full_patterns)
    # If a match against the full user input was found, generate the
    # output dict based on that match.
    output_dict = {}
    if (match_info[0]) is not REGEX_PATTERNS.NO_MATCH:
        output_dict = _generate_output_from_pattern_key(match_info[0], match_info[1])
    # Otherwise, analyze the user input for a partial match.
    else:
        output_dict = _generate_output_for_partial_or_no_match(command)
    return output_dict












# Resources used in writing this module:
# https://stackoverflow.com/questions/6343330/importing-a-long-list-of-constants-to-a-python-file
# https://stackoverflow.com/questions/6797984/how-to-convert-string-to-lowercase-in-python
# https://stackoverflow.com/questions/5843518/remove-all-special-characters-punctuation-and-spaces-from-string
# https://docs.python.org/2/library/re.html
# https://stackoverflow.com/questions/22741526/how-do-i-turn-a-list-of-words-into-a-sentence-string
# https://www.tutorialspoint.com/python/string_join.htm
# https://stackoverflow.com/questions/3294889/iterating-over-dictionaries-using-for-loops
# https://stackoverflow.com/questions/11789877/regexp-match-sequence-that-not-contains-list-of-words-net
# https://stackoverflow.com/questions/1546226/a-simple-way-to-remove-multiple-spaces-in-a-string-in-python
# https://stackoverflow.com/questions/743806/how-to-split-a-string-into-a-list