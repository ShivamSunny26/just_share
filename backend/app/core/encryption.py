import re


# 2. Chat Text Protection (Playfair Cipher)
def _generate_playfair_matrix(key: str) -> list:
    """Generates a 5*5 matrix from a secret key. J is replaced by I"""
    key = key.upper().replace("J", "I")
    # keep only alphabetical characters
    key = re.sub(r"[^A-Z]", "", key)

    # Build unique character sequence
    seen = set()
    matrix_chars = []

    # first, append key characters
    for char in key:
        if char not in seen:
            seen.add(char)
            matrix_chars.append(char)

    # Then, append the remaining alphabet (exclduing J)
    alphabet = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
    for char in alphabet:
        if char not in seen:
            seen.add(char)
            matrix_chars.append(char)

    # Chunk into 5*5 grid
    return [matrix_chars[i:i+5] for i in range(0,25,5)]

def _find_position(matrix: list, char: str)-> tuple:
    """Helper to find the (row, col) coordinates of a character."""
    for row in range(5):
        for col in range(5):
            if matrix[row][col] == char:
                return row, col
    return 0, 0


def playfair_encrypt(plain_text: str, key: str) -> str:
    """Encrypt text using the classic Playfair cipher mechanism."""
    matrix = _generate_playfair_matrix(key)

    # Standardize input text
    text = plain_text.upper().replace("J", "I")
    text = re.sub(r"[^A-Z]", "", text)

    # Prepare digrams (pairs)
    prepared_text = ""
    i = 0
    
    while i < len(text):
        char1 = text[i]
        if i + 1 < len(text):
            char2 = text[i+1]
            if char1 == char2:
                # Insert filler character "X" if letters match in a pair
                prepared_text += char1 + "X"
                i += 1
            else:
                prepared_text += char1 + char2 
                i+=2

        else:
            # Pad terminal odd character with "X"
            i += 1

    cipherr_text =""
    for k in range(0, len(prepared_text), 2):
        r1, c1 = _find_position(matrix, prepared_text[k])
        r2, c2 = _find_position(matrix, prepared_text[k+1])

        if r1 == r2: # Same Row: Shift right circular
            cipher_text += matrix[r1][(c1+1) % 5] + matrix[r2][(c2+1)% 5]
        elif c1 == c2: # Same Column: Shift down circular
            cipher_text += matrix[(r1+1) % 5][c1] + matrix[(r2+1) % 5][c2]
        else:
            cipher_text += matrix[r1][c2] + matrix[r2][c1]
    return cipher_text

def playfair_decrypt(cipher_text: str, key: str) -> str:
    """Decrypts a playfair cipher text back into upperrcase text."""
    matrix = _generate_playfair_matrix(key)
    cipher_text = cipher_text.upper().replace("J", "I")

    plain_text = ""
    for k in range(0, len(cipher_text), 2):
        r1, c1 = _find_position(matrix, cipher_text[k])
        r2, c2 = _find_position(matrix, cipher_text[k+1])

        if r1 == r2:
            plain_text += matrix[r1][(c1 - 1) % 5] + matrix[r2][(c2-1)%5]
        elif c1 == c2: 
            plain_text += matrix[(r1 - 1) % 5][c1] + matrix[(r2-1) % 5][c2]
        else:
            plain_text += matrix[r1][c2] + matrix[r2][c1]

    return plain_text