import pytest
import unittest.mock as mock

import tilemapbase.ordnancesurvey as ons
import os

def test_project():
    assert ons.project(-1.55532, 53.80474) == pytest.approx((429383.15535285, 434363.0962841))
    assert ons.project(-5.71808, 50.06942) == pytest.approx((134041.0757941, 25435.9074222))
    assert ons.project(-3.02516, 58.64389) == pytest.approx((340594.489913, 973345.118179))
    
def test_to_os_national_grid():
    assert ons.to_os_national_grid(-1.55532, 53.80474) == ("SE 29383 34363",
        pytest.approx(0.155352845), pytest.approx(0.096284069))
    assert ons.to_os_national_grid(-5.71808, 50.06942) == ("SW 34041 25435",
        pytest.approx(0.0757940984), pytest.approx(0.90742218543))
    assert ons.to_os_national_grid(-3.02516, 58.64389) == ("ND 40594 73345",
        pytest.approx(0.4899132418), pytest.approx(0.118179377))

def test_os_national_grid_to_coords():
    assert ons.os_national_grid_to_coords("SE 29383 34363") == (429383, 434363)
    assert ons.os_national_grid_to_coords("SW 34041 25435") == (134041, 25435)
    assert ons.os_national_grid_to_coords("ND 40594 73345") == (340594, 973345)
    with pytest.raises(ValueError):
        assert ons.os_national_grid_to_coords("IXJ23678412 123 12")

def test_init():
    ons.init(os.path.join("tests", "test_os_map_data"))
    base = os.path.abspath(os.path.join("tests", "test_os_map_data", "data"))

    assert ons._openmap_local_lookup == {
        "AH" : os.path.join(base, "one"),
        "AA" : os.path.join(base, "two") }
    assert ons._vectormap_local_lookup == {
        "BG" : os.path.join(base, "one") }

@pytest.fixture
def omll():
    files = {"SE" : "se_dir"}
    with mock.patch("tilemapbase.ordnancesurvey._openmap_local_lookup", new=files):
        yield None

@pytest.fixture
def image_mock():
    with mock.patch("tilemapbase.ordnancesurvey._Image") as i:
        yield i

def test_OpenMapLocal(omll, image_mock):
    oml = ons.OpenMapLocal()

    oml("SE 12345 54321")
    image_mock.open.assert_called_with(os.path.join("se_dir", "SE15SW.tif"))

    oml("SE 16345 54321")
    image_mock.open.assert_called_with(os.path.join("se_dir", "SE15SE.tif"))

    oml("SE 22345 55321")
    image_mock.open.assert_called_with(os.path.join("se_dir", "SE25NW.tif"))

    oml("SE 15345 75321")
    image_mock.open.assert_called_with(os.path.join("se_dir", "SE17NE.tif"))

    with pytest.raises(ons.TileNotFoundError):
        oml("SF 1456 12653")

    with pytest.raises(ValueError):
        oml("SF 145612653")

    assert oml.tilesize == 5000
    assert oml.tilesize == 5000

def test_Extent_construct():
    ons.Extent(429383, 430000, 434363, 440000)

    with pytest.raises(ValueError):
        ons.Extent(-1200000, 430000, 434363, 440000)

    ex = ons.Extent.from_centre(1000, 0, 1000, 4000)
    assert ex.xrange == (500, 1500)
    assert ex.yrange == (-2000, 2000)

    ex = ons.Extent.from_centre(1000, 0, 1000, aspect=2.0)
    assert ex.xrange == (500, 1500)
    assert ex.yrange == (-250, 250)
    
    ex = ons.Extent.from_centre_lonlat(-1.55532, 53.80474, 2000)
    assert ex.xrange == pytest.approx((428383.15535285, 430383.15535285))
    assert ex.yrange == pytest.approx((433363.0962841, 435363.0962841))

    ex = ons.Extent.from_lonlat(-5.71808, -1.55532, 53.80474, 50.06942)
    assert ex.xrange == pytest.approx((134041.075794, 429383.15535285))
    assert ex.yrange == pytest.approx((25435.907422, 434363.0962841))

    ex = ons.Extent.from_centre_grid("ND 40594 73345", ysize=2000, aspect=0.5)
    assert ex.xrange == (340094, 341094)
    assert ex.yrange == (972345, 974345)

def test_Extent_mutations():
    # 1000 x 5000
    ex = ons.Extent(1000, 2000, 4000, 9000)
    ex1 = ex.with_centre(10000, 20000)
    assert ex1.xrange == (10000-500, 10000+500)
    assert ex1.yrange == (20000-2500, 20000+2500)

    ex2 = ex.with_centre_lonlat(-3.02516, 58.64389) 
    assert ex2.xrange == pytest.approx((340094.489913, 341094.489913))
    assert ex2.yrange == pytest.approx((973345.118179-2500, 973345.118179+2500))

    ex3 = ex.to_aspect(2.0)
    assert ex3.xrange == (1000, 2000)
    assert ex3.yrange == (6500-250, 6500+250)
    ex3 = ex.to_aspect(0.5)
    assert ex3.xrange == (1000, 2000)
    assert ex3.yrange == (6500-1000, 6500+1000)
    ex3 = ex.to_aspect(0.1)
    assert ex3.xrange == (1250, 1750)
    assert ex3.yrange == (4000, 9000)

    ex4 = ex.with_absolute_translation(100, 200)
    assert ex4.xrange == (1100, 2100)
    assert ex4.yrange == (4200, 9200)

    ex5 = ex.with_translation(0.5, 1)
    assert ex5.xrange == (1500, 2500)
    assert ex5.yrange == (9000, 14000)
    
    ex6 = ex.with_scaling(0.5)
    assert ex6.xrange == (1500 - 1000, 2500)
    assert ex6.yrange == (6500 - 5000, 6500 + 5000)

@pytest.fixture
def source():
    s = mock.Mock()
    s.size_in_meters = 1000
    s.tilesize = 2000
    return s

def test_Plotter_plotlq(source):
    ex = ons.Extent(1100, 1900, 4200, 5500)
    plotter = ons.Plotter(ex, source)
    ax = mock.Mock()
    plotter.plotlq(ax, bob="fish")

    assert source.call_args_list == [
        mock.call("SV 1000 4000"), mock.call("SV 1000 5000") ]
    assert ax.imshow.call_args_list == [
        mock.call(source.return_value, interpolation="lanczos", extent=(1000, 2000, 4000, 5000), bob="fish"),
        mock.call(source.return_value, interpolation="lanczos", extent=(1000, 2000, 5000, 6000), bob="fish")
        ]

def test_Plotter_as_one_image(source, image_mock):
    ex = ons.Extent(1100, 1900, 4200, 5500)
    plotter = ons.Plotter(ex, source)
    ax = mock.Mock()
    out = plotter.as_one_image()

    assert source.call_args_list == [
        mock.call("SV 1000 4000"), mock.call("SV 1000 5000") ]
    image_mock.new.assert_called_with("RGB", (2000, 4000))
    im = image_mock.new.return_value
    assert out is im
    assert im.paste.call_args_list == [
        mock.call(source.return_value, (0, 2000)),
        mock.call(source.return_value, (0, 0))
        ]
