#!/usr/bin/env python3
# Generate create.sql, which is then used to setup the initial
# database.

import random
import sys

from datetime import timedelta, datetime


# SQL settings
dbname = "yiang_highscore"


def Main(test_data=False):

    out = open("create.sql","wt")
    out.write("""

CREATE DATABASE IF NOT EXISTS {dbname};
CONNECT {dbname};

CREATE TABLE IF NOT EXISTS entries (
   unique_id INT AUTO_INCREMENT PRIMARY KEY,
   score INT UNSIGNED,
   player VARCHAR(64) NOT NULL,
   country CHAR(2) NOT NULL,
   date DATETIME

);


    """.format(dbname=dbname))

    # http://stackoverflow.com/questions/553303/generate-a-random-date-between-two-other-dates
    def random_date(start, end):
        """
        This function will return a random datetime between two datetime 
        objects.
        """
        delta = end - start
        int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
        random_second = random.randrange(int_delta)
        return (start + timedelta(seconds=random_second))


    maxlen = 32
    size = 10000
    charset_high = "abcdefghijklmnopqrstuvqxyzABCDEFGHIJKLNOPQRSTUVWXYZ"
    charset_low = "_?.0123456789[](){}=-"
    countries = ["DE","UK","BE","AS","NE","AU","CH","RU"]

    d1 = datetime.strptime('1/1/1805 1:30 PM', '%m/%d/%Y %I:%M %p')
    d2 = datetime.strptime('1/1/2011 4:50 AM', '%m/%d/%Y %I:%M %p')

    for n in range(size):

        length = random.randint(0,maxlen-1)
        name = ""
        parts = random.randint(1,3)
        for p in range(parts):
            name += " " + "".join(random.choice(charset_high if random.random() > 0.1 else charset_low) for i in range(
                max(2,min(length - len(name) ,int( length/parts )
            ))))
            
        player = name.strip()
        score = random.randint(0,100000000)
        country = random.choice(countries)
        date = str(random_date(d1,d2))

        out.write("INSERT INTO entries VALUES(0, {score}, '{player}', '{country}', '{date}');\n".format(**locals()))

    out.close()



if __name__ == "__main__":
    Main(True if "test_data" in sys.argv else False)
    print("Done")

    
    
