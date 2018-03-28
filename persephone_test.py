import logging
import logging.config

logging.config.fileConfig("logging.ini")

import os
from os.path import join
from pathlib import Path
import subprocess

from persephone import corpus
from persephone import run
from persephone import corpus_reader
from persephone import rnn_ctc
from persephone.context_manager import cd
from persephone.datasets import na

EXP_BASE_DIR = "testing/exp/"
DATA_BASE_DIR = "testing/data/"

# TODO This needs to be uniform throughout the package and have a single point
# of control, otherwise the test will break when I change it elswhere. Perhaps
# it should have a txt extension.
TEST_PER_FN = "test/test_per" 

def set_up_base_testing_dir():
    """ Creates a directory to store corpora and experimental directories used
    in testing. """

    if not os.path.isdir(EXP_BASE_DIR):
        os.makedirs(EXP_BASE_DIR)
    if not os.path.isdir(DATA_BASE_DIR):
        os.makedirs(DATA_BASE_DIR)

def rm_dir(path: Path):

    import shutil
    if path.is_dir():
        shutil.rmtree(str(path))

def download_example_data(example_link):
    """
    Clears DATA_BASE_DIR, collects the zip archive from example_link and unpacks it into
    DATA_BASE_DIR.
    """

    # Prepare data and exp dirs
    set_up_base_testing_dir()
    zip_fn = join(DATA_BASE_DIR, "data.zip")
    if os.path.exists(zip_fn):
        os.remove(zip_fn)

    # Fetch the zip archive
    import urllib.request
    urllib.request.urlretrieve(example_link, filename=zip_fn)

    # Unzip the data
    import subprocess
    args = ["unzip", zip_fn, "-d", DATA_BASE_DIR]
    subprocess.run(args, check=True)

def get_test_ler(exp_dir):
    """ Gets the test LER from the experiment directory."""

    test_per_fn = join(exp_dir, TEST_PER_FN)
    with open(test_per_fn) as f:
        ler = float(f.readlines()[0].split()[-1])

    return ler

# Only the tutorial test actually should need to pull the data; the rest can be
# lazy and assume the data hasn't changed (which is pretty reasonable)
def test_tutorial():
    """ Tests running the example described in the tutorial in README.md """

    # 1024 utterance sample set.
    NA_EXAMPLE_LINK = "https://cloudstor.aarnet.edu.au/plus/s/YJXTLHkYvpG85kX/download"
    na_example_dir = join(DATA_BASE_DIR, "na_example/")
    rm_dir(Path(na_example_dir))

    download_example_data(NA_EXAMPLE_LINK)

    # Test the first setup encouraged in the tutorial
    corp = corpus.ReadyCorpus(na_example_dir)
    exp_dir = run.train_ready(corp, directory=EXP_BASE_DIR)

    # Assert the convergence of the model at the end by reading the test scores
    ler = get_test_ler(exp_dir)
    assert ler < 0.3

def test_fast():
    """
    A fast integration test that runs 1 training epoch over a tiny
    dataset. Note that this does not run ffmpeg to normalize the WAVs since
    Travis doesn't have that installed. So the normalized wavs are included in
    the feat/ directory so that the normalization isn't run.
    """

    # 4 utterance toy set
    TINY_EXAMPLE_LINK = "https://cloudstor.aarnet.edu.au/plus/s/g2GreDNlDKUq9rz/download"
    tiny_example_dir = join(DATA_BASE_DIR, "tiny_example/")
    rm_dir(Path(tiny_example_dir))

    download_example_data(TINY_EXAMPLE_LINK)

    corp = corpus.ReadyCorpus(tiny_example_dir)

    exp_dir = run.prep_exp_dir(directory=EXP_BASE_DIR)
    model = run.get_simple_model(exp_dir, corp)
    model.train(min_epochs=2, max_epochs=5)

    # Assert the convergence of the model at the end by reading the test scores
    ler = get_test_ler(exp_dir)
    # Can't expect a decent test score but just check that there's something.
    assert ler < 2.0



test_tutorial()
