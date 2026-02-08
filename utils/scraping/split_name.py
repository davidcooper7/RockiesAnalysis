def split_name(name):
        try:
            first, last = name.split()
        except:
            first, last = name.split()[0], ' '.join(name.split()[1:])

        return last, first