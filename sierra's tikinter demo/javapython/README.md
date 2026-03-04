Sierra Norstrom and James Pickens
CMPS-4143-102 TopContProgLang: Java/Python Fall Sem 2025

About Program:
     This is a Python program that inputs data from a text file named 'log.txt' and splits it into lines, and then splits those lines into parts to analyze for information (emails, IP addresses, date/time stamps, actions, errors)

For each line of the input file processed, it adds 1 to a 'Total Lines' counter
For each line of the input file that is correctly formatted, it adds 1 to a 'Valid Lines' Counter
   A line is deemed correct if it contains a timestamp/email/ip/error that fits the regex pattern
For each line of the input file that is incorrectly formatted, it adds 1 to a 'Invalid Lines' Counter
   A line is deemed incorrect if it does not have any timestamp/email/ip/error that fits the regex pattern

The Program finds each properly formatted email and counts if they managed to login successfully or not, printing them out
Counts each error (does not count improper formatting as an error) and adds it to a 'Errors detected' counter
Counts each IP, if it is not repeated then a 'Unique IPs' counter is added to