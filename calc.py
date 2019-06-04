import sys
import json
import jsonschema
import numpy

TILES = 34
TRANS = {'m':0, 'M':0, 'p':9, 'P':9, 's':18, 'S':18, 'z':27}

class Stat(object):
  def __init__(self):
    self.prob = {}
    self.score = {}

def set_hand(hai):
  hand = [0]*TILES
  suite = 0

  for elem in reversed(hai):
    try:
      num = suite+int(elem)-1
      hand[num] = hand[num]+1
    except:
      suite = TRANS[elem]
  return hand

def trans(tile):
  return int(tile[0])+TRANS[tile[1]]-1

def calc_rate(tiles, turns, inflow, outflow):
  depth = len(outflow)+1
  rate = numpy.zeros((depth, turns))
  rate[0][0] = 1

  for k in range(0, turns-1):
    rate[0][k+1] = (1-outflow[0]/(tiles-k))*rate[0][k]

    for j in range(1, depth-1):
      rate[j][k+1] = (1-outflow[j]/(tiles-k))*rate[j][k]+inflow[j-1]/(tiles-k)*rate[j-1][k]
    
    rate[-1][k+1] = inflow[-1]/(tiles-k)*rate[-2][k]+rate[-1][k]
  
  return rate[-1]

def calc(hand, wall, tiles, turns, inflow, outflow, data, stat):
  num1 = -1
  num2 = -1

  if 'tsumo' in data:
    num1 = trans(data['tsumo'])
    inflow.append(wall[num1])
    hand[num1] = hand[num1]+1
    wall[num1] = wall[num1]-1
  if 'dahai' in data:
    num2 = trans(data['dahai'])
    hand[num2] = hand[num2]-1

  if 'label' in data:
    label = data['label']
    value = calc_rate(tiles, turns, inflow, outflow)

    for elem in label:
      stat.prob[elem] = stat.prob[elem]+value if elem in stat.prob.keys() else value

    if 'score' in data:
      for elem in label:
        stat.score[elem] = stat.score[elem]+data['score']*value if elem in stat.score.keys() else data['score']*value

  if 'nodes' in data:
    outflow.append(0)

    for elem in data['nodes']:
      outflow[-1] = outflow[-1]+wall[trans(elem['tsumo'])]

    for elem in data['nodes']:
      calc(hand, wall, tiles, turns, inflow, outflow, elem, stat)

  if num1 != -1:
    hand[num1] = hand[num1]-1
    wall[num1] = wall[num1]+1
    inflow.pop()

  if num2 != -1:
    hand[num2] = hand[num2]+1
    outflow.pop()

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print('There are too few arguments.')
    sys.exit(1)

  with open('base.json') as f:
    base = json.load(f)

  with open(sys.argv[1], 'r') as g:
    data = json.load(g)

  try:
    jsonschema.validate(data,base)
  except Exception as e:
    print('A validation error occurred.')
    sys.exit(1)

  print('Enter the remaining turns.')
  turns = int(input())+1
  print()

  hand = set_hand(data['hai'])
  wall = [4 - i for i in hand]
  inflow = []
  outflow = [0]
  stat = Stat()

  if 'dahai' in data:
    num = trans(data['dahai'])
    hand[num] = hand[num]-1

  for elem in data['nodes']:
    outflow[0] = outflow[0]+wall[trans(elem['tsumo'])]
  for elem in data['nodes']:
    calc(hand, wall, sum(wall), turns, inflow, outflow, elem, stat)

  labels_prob = sorted(stat.prob.keys())
  labels_score = sorted(stat.score.keys())

  print('Hai:', data['hai'])

  if len(labels_prob) > 0:
    print('Probability:')
    print('Turn', '\t'.join(labels_prob), sep='\t')

    for turn in range(1, turns):
      print(turn, end='\t')
      for label in labels_prob:
        print('{:.3g}'.format(stat.prob[label][turn]), end='\t')
      print()

  if len(labels_score) > 0:
    print('Score:')
    print('Turn', '\t'.join(labels_score), sep='\t')

    for turn in range(1, turns):
      print(turn, end='\t')
      for label in labels_score:
        print('{:.3g}'.format(stat.score[label][turn]), end='\t')
      print()
