def get_token():
    file = open("token.txt", 'r')
    token = file.readline()
    token = token.rstrip('\n')
    return token
