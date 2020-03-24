"""
Module to run tests on FlatField class
Requires files in Development suite and an Environmental variable
"""
import os

import pytest
import glob
import numpy as np

from astropy.io import fits

from pypeit.tests.tstutils import dev_suite_required, load_kast_blue_masters, cooked_required
from pypeit import flatfield
from pypeit.par import pypeitpar
from pypeit.spectrographs.util import load_spectrograph
from pypeit.images import pypeitimage

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'files')
    return os.path.join(data_dir, filename)


# TODO: Bring this test back in some way?
#def test_step_by_step():
#    if skip_test:
#        assert True
#        return
#    # Masters
#    spectrograph, TSlits, tilts, datasec_img \
#                = load_kast_blue_masters(get_spectrograph=True, tslits=True, tilts=True,
#                                         datasec=True)
#    # Instantiate
#    flatField = flatfield.FlatField(spectrograph, det=1, tilts=tilts,
#                                    tslits_dict=TSlits.tslits_dict.copy())
#    # Use mstrace
#    flatField.mspixelflat = TSlits.mstrace.copy()
#    # Normalize a slit
#    slit=0
#    flatField._prep_tck()
#    modvals, nrmvals, msblaze_slit, blazeext_slit, iextrap_slit = flatField.slit_profile(slit)
#    assert np.isclose(iextrap_slit, 0.)
#    # Apply
#    word = np.where(flatField.tslits_dict['slitpix'] == slit + 1)
#    flatField.mspixelflatnrm = flatField.mspixelflat.copy()
#    flatField.mspixelflatnrm[word] /= nrmvals
#    assert np.isclose(np.median(flatField.mspixelflatnrm), 1.0267346)

def test_flatimages():
    tmp = np.ones((1000, 100)) * 10.
    instant_dict = dict(procflat=tmp,
                        pixelflat=np.ones_like(tmp),
                        illumflat=np.ones_like(tmp),
                        flat_model=None)

    flatImages = flatfield.FlatImages(**instant_dict)
    assert flatImages.flat_model is None

    # I/O
    outfile = data_path('tst_flatimages.fits')
    flatImages.to_file(outfile, overwrite=True)
    _flatImages = flatfield.FlatImages.from_file(outfile)
    # Test
    for key in instant_dict.keys():
        if isinstance(instant_dict[key], np.ndarray):
            assert np.array_equal(flatImages[key],_flatImages[key])
        else:
            assert flatImages[key] == _flatImages[key]

@cooked_required
def test_run():
    # Masters
    spectrograph = load_spectrograph('shane_kast_blue')
    edges, waveTilts = load_kast_blue_masters(edges=True, tilts=True)
    # Instantiate
    par = spectrograph.default_pypeit_par()
    rawflatimg = pypeitimage.PypeItImage(edges.img.copy())
    # TODO -- We would want to save the detector if we ever planned to re-run from EdgeTrace
    hdul = fits.HDUList([])
    rawflatimg.detector = spectrograph.get_detector_par(hdul, 1)
    flatField = flatfield.FlatField(rawflatimg, spectrograph, par['calibrations']['flatfield'],
                                    wavetilts=waveTilts, slits=edges.get_slits())

    # Use the trace image
    flatImages = flatField.run()
    assert np.isclose(np.median(flatImages.pixelflat), 1.0)

