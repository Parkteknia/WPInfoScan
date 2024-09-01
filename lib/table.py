#https://stackoverflow.com/a/77820161
from .colors import colors
def colorize(token, bold_and_al='', fg_color='', bg_color=''):
    prefix = '\x1b['
    suffix = 'm'
    reset = '\x1b[0m'

    return '\x1b[' + bold_and_al + ";" + fg_color + ";" + bg_color + "m" + token + reset

def pretty_print_table(rows, line_between_rows=False):
  """
  Example Output
  ┌──────┬─────────────┬────┬───────┐
  │ True │ short       │ 77 │ catty │
  ├──────┼─────────────┼────┼───────┤
  │ 36   │ long phrase │ 9  │ dog   │
  ├──────┼─────────────┼────┼───────┤
  │ 8    │ medium      │ 3  │ zebra │
  └──────┴─────────────┴────┴───────┘
  """

  # find the max length of each column
  max_col_lens = list(map(max, zip(*[(len(str(cell)) for cell in row) for row in rows])))
  # print the table's top border
  print('┌' + '┬'.join('─' * (n + 2) for n in max_col_lens) + '┐')

  rows_separator = '├' + '┼'.join('─' * (n + 2) for n in max_col_lens) + '┤'

  row_fstring = ' │ '.join("\033[91m{: <%s}\033[00m" % n for n in max_col_lens)

  for i, row in enumerate(rows):
    print('│', row_fstring.format(*map(str, row)), '│')
    
    if line_between_rows and i < len(rows) - 1:
      print(rows_separator)

  # print the table's bottom border
  print('└' + '┴'.join('─' * (n + 2) for n in max_col_lens) + '┘')
