## Translate string formatting into string interpolation

Python 3.6 introduces [F-strings](https://lwn.net/Articles/656898/)
as a new way of doing string formatting.

Instead of writing this:

```
def say(greeting='hello', target='world'):
    print('%s%s, %s!' % (greeting[0].upper(), greeting[1:], target))
```

... you can now write this:

```
def say(greeting='hello', target='world'):
    print(f'{greeting[0].upper()}{greeting[1:]}, {target}!')
```

This project provides automatic translation of old `%`-style formatting
to the new string interpolation method using F-strings.
