"""
__author__ = 'Christopher Fagiani'
"""
import logging
import argparse
import sys
from engine import workout_controller


def main(args):
    controller = None
    try:
        controller = workout_controller.WorkoutController(args.config)
        rounds, hits, misses = controller.start_workout(args.mode, args.time)
        print("Workout Complete\n=================")
        print("Hits: {hits}\nMisses: {misses}".format(hits=hits, misses=misses))

    except KeyboardInterrupt:
        print("shutting down")
    finally:
        if controller is not None:
            controller.cleanup()


def configure_logger():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)


if __name__ == "__main__":
    configure_logger()
    argparser = argparse.ArgumentParser(description="Uses LEDs to indicate which side of a punching bag to hit")
    argparser.add_argument("-c", "--config", metavar='config', default="sparpi.ini", help='Configuration file to use',
                           dest='config')
    argparser.add_argument("-w", "--workout", metavar='workout', default='random', choices=['random', 'alternating'],
                           help='Desired workout mode', dest='mode')
    argparser.add_argument("-t", "--time", metavar='time', default=2, type=float,
                           help="Time in minutes for the workout")
    main(argparser.parse_args())
