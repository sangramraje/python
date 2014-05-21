#!/usr/bin/python

from HTMLParser import HTMLParser
import json
import argparse

global trade_date
global trade_date_next
global trade_date_on_next_td
global order_info_start_row
global order_info_start
global order_info_line_count
global field_number
global FIELDS_ARR
global line_data
global line_data_map
global line_type
global complete_file_data
global trades_details
global summary_map

# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
  def handle_starttag(self, tag, attrs):
    global trade_date_on_next_td
    global trade_date_next
    global order_info_start_row
    global order_info_start
    global order_info_line_count
    global field_number
    global line_data
    global line_data_map
    global line_type
    global complete_file_data
    global trades_details
    global summary_map

    if trade_date_on_next_td:
#      print "Encountered a start tag:", tag
      if tag.startswith('td'):
        trade_date_next = True
        trade_date_on_next_td = False
    elif order_info_start_row:
#      print "Encountered a start tag in order_info_start_row:", tag
      if tag.startswith('tr'):
        order_info_line_count = order_info_line_count + 1
        field_number = -1
        if order_info_line_count % 3 == 2 or line_type == 'Summary':
          if order_info_line_count > 3:
            #print "LINE: ", line_data
            #json_line = json.dumps(line_data_map)
            #print json_line
            if line_type == 'Summary':
              if len(line_data_map) == 2:
                key = line_data_map['Summary##Security']
                if line_data_map.has_key('Summary##STT Amount'):
                  val = line_data_map['Summary##STT Amount']
                else:
                  val = line_data_map['Summary##Amount Rs']
                summary_map[key] = val
              complete_file_data['Summary'] = summary_map
            else:
              trades_details = trades_details + [line_data_map]
              complete_file_data['Trades'] = trades_details
          order_info_start = True
          line_type = 'TradeInfo'
          line_data = ''
          line_data_map = {}
        elif order_info_line_count % 3 == 0 and order_info_line_count > 0:
          line_type = 'STT_Info'
        elif order_info_line_count % 3 == 1 and order_info_line_count > 1:
          line_type = 'Total_STT'
      elif order_info_start and tag.startswith('td'):
        field_number = field_number + 1
        if field_number > 0 and line_type == 'TradeInfo' and line_data == '':
          line_type = 'Summary'


  def handle_endtag(self, tag):
    global order_info_start
    global order_info_start_row
    if order_info_start and tag.startswith('table'):
      #print "Encountered an end tag :", tag
      order_info_start = False
      order_info_start_row = False
    #if 0:
    #  print "Encountered an end tag :", tag

  def handle_data(self, data):
    global trade_date_next
    global trade_date
    global trade_date_on_next_td
    global order_info_start_row
    global order_info_start
    global field_number
    global FIELDS_ARR
    global line_data
    global line_data_map
    global line_type
    global complete_file_data

    if trade_date_next:
#      print "Encountered some data  :", data
      date_str = data
      date_str_arr = data.split('/')
#      print date_str_arr
      trade_date = int(date_str_arr[2]) * 10000 + int(date_str_arr[1]) * 100 + int(date_str_arr[0])
      trade_date_next = False
      #print "setting trade_date to " + str(trade_date)
      complete_file_data['trade_date'] = trade_date
    if data.startswith('TRADE DATE :'):
#      print "Encountered some data  :", data
      trade_date_on_next_td = True
#      print "setting trade_date_on_next_td"

    if order_info_start and len(data.strip()) > 0:
      if line_type == 'TradeInfo':
        line_data_map[FIELDS_ARR[field_number]] = data.strip()
      elif line_type == 'STT_Info' or line_type == 'Total_STT':
        line_data_map[line_type + '##' + FIELDS_ARR[field_number]] = data.strip()
      elif line_type == 'Summary':
        line_data_map[line_type + '##' + FIELDS_ARR[field_number]] = data.strip()
      line_data += '$$' + data.strip()


    if data.startswith('Order No'):
      #print "Encountered some data  :", data
      order_info_start_row = True
      order_info_start = False
      line_type = 'TradeInfo'
      line_data = ''
      line_data_map = {}



# instantiate the parser and fed it some HTML
parser = MyHTMLParser()
#parser.feed('<html><head><title>Test</title></head>'
#            '<body><h1>Parse me!</h1></body></html>')

def callParser(filename):
  global trade_date
  global trade_date_next
  global trade_date_on_next_td
  global order_info_start_row
  global order_info_start
  global order_info_line_count
  global FIELDS_ARR
  global complete_file_data
  global trades_details
  global summary_map

  file = open(filename, 'r')
  entire_file = file.read()
  trade_date = 19700101
  trade_date_next = False
  trade_date_on_next_td = False
  order_info_line_count = 0
  order_info_start_row = False
  order_info_start = False
  FIELDS_ARR = ['Order No', 'Order Time', 'Trade No.', 'Trade Time', 'Security', 'Bought Qty', 'Sold Qty', 'Gross Rate Per Security',
      'Gross Total', 'Brokerage', 'Net Rate Per Security', 'Service Tax', 'STT Amount', 'Amount Rs']
  complete_file_data = {}
  trades_details = []
  summary_map = {}
  parser.feed(entire_file)
  json_line = json.dumps(complete_file_data, sort_keys = True, indent = 4, separators = (',', ': '))
  #print "Complete Data"
  print json_line

def print_data():
  print str(trade_date)

def main():
  global complete_file_data

  parser = argparse.ArgumentParser(description='Extract information from HTML contract note into a JSON file')
  parser.add_argument('html_file', metavar='f', type=str, help='HTML filename')
  parser.add_argument('json_file', metavar='o', type=str, help='JSON filename')
  args = parser.parse_args()

  import os.path
  html_file = os.path.realpath(args.html_file)
  json_file = os.path.realpath(args.json_file)

  callParser(html_file)
  output_file = open(json_file, 'w')
  json.dump(complete_file_data, output_file, sort_keys = True, indent = 4, separators = (',', ': '))
#  json.dump(complete_file_data, output_file)
  output_file.close()

if __name__ == "__main__":
      main()
