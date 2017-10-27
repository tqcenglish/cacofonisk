from cacofonisk import DebugReporter, FileRunner

reporter = DebugReporter()
# To attach the AmiRunner
runner = FileRunner('tests/fixtures/xfer_blind/xfer_blind_no_answer.json', reporter)
# runner = FileRunner('tests/examples/orig/ab_callgroup.json', reporter)
# runner = FileRunner('tests/examples/orig/xfer_abacbc.json', reporter)
# runner = FileRunner('tests/examples/orig/xfer_blind_abacbc.json', reporter)
# runner = FileRunner('tests/examples/CallPickupAbAcManual.replay.json', reporter)
runner.run()
