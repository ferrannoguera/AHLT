import argparse
from nltk.classify import megam
import os

# DEFAULT VALUES
TRAIN = "Train"
DEVEL = "Devel"
TEST = "Test-DDI"
DEF_TRAIN_DIR = "data/" + TRAIN
DEF_DEVEL_DIR = "data/" + DEVEL
DEF_TEST_DIR = "data/" + TEST
DEF_GROUP_NAME = "ArnauCanyadell_FerranNoguera"
DEF_VERSION = "101"


def class_number_to_name(class_number):
    if class_number == "0":
        return "null"
    elif class_number == "1":
        return "mechanism"
    elif class_number == "2":
        return "effect"
    elif class_number == "3":
        return "advise"
    elif class_number == "4":
        return "int"
    raise ValueError("class name should be a number from 0 to 4 but instead found: " + str(class_number))


def output_ddi(id, id_e1, id_e2, ddi_type, outf):
    is_ddi = "0" if ddi_type == "null" else "1"
    print("|".join([id, id_e1, id_e2, is_ddi, ddi_type]), file=outf)


def evaluate(inputdir, outputfile):
    """
    Input: Receives a data directory and the filename for the
    results to evaluate. inputdir is the folder containing
    original XML (with the ground truth). outputfile is the
    file name with the entities produced by your system.

    Output: Prints statistics about the predicted entities in
    the given output file.

    Note: outputfile must match the pattern: task9.2_NAME_NUMBER.txt
    (where NAME may be any string and NUMBER any natural number).
    You can use this to encode the program version that produced the file.

    :param inputdir:
    :param outputfile:
    """
    os.system("java -jar eval/evaluateDDI.jar " + inputdir + " " + outputfile)


def predict_a_posteriori(predictions, features):
    for i in range(min(len(predictions), len(features))):
        if "int" in features[i]:
            predictions[i] = "4"
    return predictions


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputdirtrain", help="path of the train input directory", default=DEF_TRAIN_DIR)
    parser.add_argument("--inputdirdevel", help="path of the devel input directory", default=DEF_DEVEL_DIR)
    parser.add_argument("--inputdirtest", help="path of the test input directory", default=DEF_TEST_DIR)
    parser.add_argument("--testdir", help="directory for testing result", choices=["test", "devel", "train"], default="devel")
    parser.add_argument("--groupname", help="path of the output file", default=DEF_GROUP_NAME)
    parser.add_argument("--version", help="version of the algorithm", default=DEF_VERSION)
    parser.add_argument("--rulesaposteriori", help="use rules that are applied after the maxent algorithm")
    args = parser.parse_args()

    inputdir = args.inputdirdevel if args.testdir == "devel" else args.inputdirtest

    # Train
    megam.config_megam("src/megam_i686.opt")
    train = megam.call_megam(["multiclass", "features/features_megan_train_" + str(args.version) + ".txt"])
    with open("features/weights", "w") as f:
        f.write(train)

    # Prediction
    predictions_text = megam.call_megam(["-predict", "features/weights", "multiclass",
                                         "features/features_megan_" + args.testdir + "_" + str(args.version) + ".txt"])
    predictions = [y.split("\t")[0] for y in predictions_text.split("\n") if len(y) > 1]

    # Read IDs
    with open("features/features_" + args.testdir + "_" + args.version + ".txt", 'r') as f:
        ids_text = f.read()
    ids = [x.split("\t")[:3] for x in ids_text.split("\n") if len(x) > 1]

    # Custom rules "a posteriori"
    if args.rulesaposteriori:
        features = [x.split("\t")[4:] for x in ids_text.split("\n") if len(x) > 1]
        predictions = predict_a_posteriori(predictions, features)

    # Output DDIs
    output_file = "out/task9.2_" + DEF_GROUP_NAME + "_" + str(args.version) + ".txt"

    with open(output_file, 'w') as f:
        for prediction, id in zip(predictions, ids):
            output_ddi(id[0], id[1], id[2], class_number_to_name(prediction), f)

    # Evaluate
    evaluate(inputdir, output_file)
