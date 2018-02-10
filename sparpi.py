"""
__author__ = 'Christopher Fagiani'
"""
import logging
import argparse
import sys
from engine import workout_controller


def main(args):
    controller = None
    configure_logger(args.debug)
    try:
        controller = workout_controller.WorkoutController(args.config)
        if args.headless:

            workout_stats = controller.start_workout(args.mode, args.time)
            print("Workout Complete\n=================")
            print("Hits: {hits}\nMisses: {misses}".format(hits=len(workout_stats.correct_hits),
                                                          misses=len(
                                                              workout_stats.incorrect_hits) + workout_stats.timeouts
                                                          ))
        else:
            from ui.ui_server import SparpiServer
            server = SparpiServer(args.port, controller)
            server.start()

    except KeyboardInterrupt:
        print("shutting down")
    finally:
        if controller is not None:
            controller.cleanup()


def configure_logger(is_debug):
    root = logging.getLogger()
    if is_debug:
        root.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.INFO)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Uses LEDs to indicate which side of a punching bag to hit")
    argparser.add_argument("-c", "--config", metavar='config', default="sparpi.ini", help='Configuration file to use',
                           dest='config')
    argparser.add_argument("-w", "--workout", metavar='workout', default='random', choices=['random', 'alternating'],
                           help='Desired workout mode. Only used when running headless.', dest='mode')
    argparser.add_argument("-t", "--time", metavar='time', default=2, type=float,
                           help="Time in minutes for the workout. Only used when running headless.")
    argparser.add_argument("-d", "--debug", action="store_true", default=False)
    argparser.add_argument("-p", "--port", type=int, default=80,
                           help="Port on which to run the UI. Ignored if headless.")
    argparser.add_argument("-hl", "--headless", default=False, action="store_true",
                           help="If true, no ui server will be started")
    main(argparser.parse_args())
