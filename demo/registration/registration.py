
def main():

    # parse superheros list
    superheros = []
    with open('superheros.list') as f:
        for line in f:
            superheros.append(line[1:-2].lower())

    while True:
        user_in = raw_input().lower()

        # if it is a string, find matches. List by number

        # if it is a number, pick one of those matches

        # if it is enter, pick the only match if there was just one

        matches = []
        for hero in superheros:
            if hero.startswith(user_in):
                matches.append(hero)

        print(matches)
    



if __name__ == '__main__':
    main()
