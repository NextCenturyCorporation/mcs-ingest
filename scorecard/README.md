
# Scorecard

Given an output json from a run, create a 'scorecard' which evaluates the motion of the
agent in several dimensions.

The actions that are counted (as of Eval 4 plan):

* Revisiting parts of the room that have not changed
* Attempting to open an un-openable object.
  * We will begin counting from the first attempt
* Looking into the same container repeatedly
* Target object in the field of view but agent does not move toward it
  * After a certain number of frames, not moving toward a visible target object will be counted
* Repeating a failed action.
  * We will begin counting from the second attempt, since it cannot be a “failed” action until after the AI has received
  feedback from the first attempt. If the AI system attempts the same action from a new position, this will not be considered a repeated action.
* Attempting physically impossible actions.
  * e.g., trying to pick up a sofa or another similarly large item; trying to interact with the floor or wall
  * Impossible actions will be counted from the first attempt.

Some of these are mathematically vague;  for example, the space that the agent moves in is continous,
so 'revisit' needs to have a particular distance.  Below, we discuss the way to count them.

# Algorithms

#### Revisiting parts of the Room

Algorithm:
* Divide room (10m x 10m) into a grid of X size.  Try 0.5 m
* Count the number of times that the agent enters a
grid square while facing in the same direction (within 10 degrees) as a
previous time they were in that grid square
* If paths cross while facing in different directions, it does not count as a revist
* If the actor rotates or does not move (PASS), it does not count
  * Note that this means that if the actor spins in a circle and then passes over
    that location in any direction later, it will count as a revist
* Note:  if agent travels from point A to point B twice, this can result in many overlaps.
  * They only count as one.
  * Implement this as only counting the first in a series of revisits.

#### Attempting to Open an UnOpenable object

This counts the number of times that the agent tried to open something
and failed because it was something they were not supposed to be
openning.

Notably, this does _not_ include IS_OPENED_COMPLETELY which is what
is returned if you try to open an already-opened object and OUT_OF_REACH
which is returned when you try to open an openable object but it is
too far away.  Everything else causes the count of unopenable objects to
increase.

#### Looking into the Same Container Repeatedly

If the agent looks in the same container repeatedly, count it (after the
first look).  Algorithm:
* If the agent goes up to a container and OPENs it, that counts as the
first time
* If the agent goes to the open container and looks down
into the container, that counts as a second time
  * Looking down requires tilt >= 30 and the gaze point to be
  within 0.4 of the container
* If the agent closes the container and then re-opens, it still counts
* Moving around / tilting while looking in the container only counts as a
single look.  This is implemented by ignoring the next 10 movements and setting
a flag that they are still looking
* Passing the container without looking into it does not count

Note:   The orientation of the container is not being taken into account.  That is,
if the container was opened but the hinge of the lid was facing the agent so
they could not see into it, then it still counts as the first time.  Going around
the container so that they can actually look into it counts as a second look.
It is recognized that this is a limitation of the algorithm.

#### Target object in the field of view but agent does not move toward it

If the agent can see the target object, it should move toward it.  This is slightly
more complicated than that because there might be objects in the way or the target may not 
be very visible (a single pixel on the edge of the field of view). 

Algorithm:
  * The target needs to be visible for a number of frames in a row (4) before it counts 
  as being sufficiently visible that the agent should have seen it.  A timer is then
  started and the distance to the target is saved   
  * After 30 steps, the agent should have had time to go around whatever is in the way
  and moved closer to the target.  
  * If it doesn't move towards the target, then we increment by one and reset
  * If it does move towards the target, it needs to continue moving towards 
  the target (within the next 30 steps)
  
The number 30 is to give the agent sufficient time to go around an obstacle. We 
ignore turns, passes, tilts, etc and only count MoveAhead, MoveBack, MoveLeft, 
and MoveRight.  It takes maybe 15 steps to the side to get past an object 
(during which distance will increase), and then some number of steps to make 
up for the fact that the agent was moving away while going around the obstacle 
(15).  Based on some testing, 30 is about right.  


#### Repeated Failed Actions

If the agent repeatedly tries an action and fails, then it should be counted.  In 
terms of what it means to 'repeat' an action, it needs to occur:
 * Facing the same object, or 
 * From approximately the same place and facing the same direction

Note that this overlaps with some of the other scorecard elements.  For example,
attempting to open an unopenable object will cause it to count in that category.
This one will count if the agent tries to do it twice (or more times).  If the 
agent does it twice, then the unopenable object count will be 2 and the 
repeated failed actions will 

## Running the Scorecard


The file ```tests/scorecard_test_ground_truth.py``` shows an example of how to run the
scorecard code:  You create a Scorecard object, passing in the scene json file
along with the json file with the MCS history output, and then tell it to score all
the parts of the scorecard: 

```
scorecard = Scorecard(scene_json_filepath, ouput_json_filepath)
scorecard_dict = scorecard.score_all()
```

For testing and experimentation, you can tell it calculate the 
score for particular parts of the scorecard: 

```
scorecard = Scorecard(scene_json_filepath, ouput_json_filepath)
num_revisit_calc = scorecard.calc_revisiting()
```



## Testing the Scorecard

The scorecard has normal unit tests in ```tests/test_scorecard.py```.

The scorecard also has an integration test```test/test_scorecard_ground_truth.py```.   That
code uses data generated by a series of generators, one per type of actions counted
above.

The outputs of the generators will be a series of history files in
```test_data_generator/SCENE_HISTORY```.  Those are then read in by the integration
test and the output compared  with the values in
```tests/scorecard_ground_truth.txt```.  Running the integration test:

```
% PYTHONPATH='.' python tests/test_scorecard_ground_truth.py
```

Note that the generators use scene files, since the generator is running the
MCS software and needs a scene relevant for the scorecard test.  The scene files
have been modified from the original used in the evaluation in 2 ways:
1. The roomDimensions object has been added. For testing, they are 10,11,12; they were 10,10,10
1. Objects have been moved and the starting point for the agent has sometimes been
moved.

### Reopen Generator ###

To use the revisit generator:

```
% PYTHONPATH='.' python test_data_generator/scorecard_generate_reopen_data.py [MCS_unity] [scene_file]
```

Use `tests/golf_0018_15_debug.json`

### Revisit Generator ###

To use the revisit generator:

```
% PYTHONPATH='.' python test_data_generator/scorecard_generate_revisit_data.py [MCS_unity] [scene_file]
```

The scene_file to use should be `tests/india_0003_17.json`.

### Opening UnOpenable Objects

To use the unopenable generator:
```
% PYTHONPATH='.' python test_data_generator/scorecard_generate_unopenable_data.py [MCS_unity] [scene_file]
```

The scene_file to use should be `tests/golf_0018_15_debug.json` which has
both openable and unopenable objects.
