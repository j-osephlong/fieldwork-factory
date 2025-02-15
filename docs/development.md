Development of fieldwork-bakery plugin
===========================

This project uses [qgis_plugin_tools](https://github.com/j-osephlong/qgis_plugin_tools) submodule,
so set git setting value: `git config --global submodule.recurse true`.

When cloning use `--recurse-submodules` like so:
`git clone --recurse-submodules https://github.com/j-osephlong/fieldwork-bakery.git`

When pulling from existing repo:
```sh
git submodule init
git submodule update
```


The code for the plugin is in the [fieldworkbakery](../fieldwork-bakery) folder. Make sure you have required tools, such as
Qt with Qt Editor and Qt Linquist installed by following this
[tutorial](https://www.qgistutorials.com/en/docs/3/building_a_python_plugin.html#get-the-tools).

For building the plugin use platform independent [build.py](../fieldwork-bakery/build.py) script.

## Setting up development environment

To get started with the development, follow these steps:

1. Go to the  [fieldworkbakery](../fieldwork-bakery) directory with a terminal
1. Create a new Python virtual environment with pre-commit using Python aware of QGIS libraries:
   ```shell
    python build.py venv
    ```
   In Windows it would be best to use python-qgis.bat or python-qgis-ltr.bat:
   ```shell
    C:\OSGeo4W64\bin\python-qgis.bat build.py venv
   ```
1. **Note: This part is  only for developers that are using QGIS < 3.16.8.** If you want to use IDE for development, it is best to start it with the
   following way on Windows:
   ```shell
    :: Check out the arguments with python build.py start_ide -h
    set QGIS_DEV_IDE=<path-to-your-ide.exe>
    set QGIS_DEV_OSGEO4W_ROOT=C:\OSGeo4W64
    set QGIS_DEV_PREFIX_PATH=C:\OSGeo4W64\apps\qgis-ltr
    C:\OSGeo4W64\bin\python-qgis.bat build.py start_ide
    :: If you want to create a bat script for starting the ide, you can do it with:
    C:\OSGeo4W64\bin\python-qgis.bat build.py start_ide --save_to_disk
   ```

Now the development environment should be all-set.

If you want to edit or disable some quite strict pre-commit scripts, edit .pre-commit-config.yaml.
For example to disable typing, remove mypy hook and flake8-annotations from the file.

## Keeping dependencies up to date

1. Activate the virtual environment.
2. `pip install pip-tools`
3. `pip-compile --upgrade requirements-dev.in`
4. `pip install -r requirements-dev.txt` or `pip-sync requirements-dev.txt`

## Adding or editing  source files

If you create or edit source files make sure that:

* they contain absolute imports:
    ```python
    from fieldworkbakery.utils.exceptions import TestException # Good

    from ..utils.exceptions import TestException # Bad

    ```
* they will be found by [build.py](../fieldworkbakery/build.py) script (`py_files` and `ui_files` values)

* you consider adding test files for the new functionality
## Deployment

Edit [build.py](../fieldworkbakery/build.py) to contain working values for *profile*, *lrelease* and *pyrcc*. If you are
running on Windows, make sure the value *QGIS_INSTALLATION_DIR* points to right folder

Run the deployment with:

```shell script
python build.py deploy
```

After deploying and restarting QGIS you should see the plugin in the QGIS installed plugins where you have to activate
it.


## Testing

Install python packages listed in [requirements-dev.txt](../requirements-dev.txt) to the virtual environment
and run tests with:

```shell script
pytest
```

## Translating

### Translating with Transifex

Fill in `transifex_coordinator` (Transifex username) and `transifex_organization`
in [.qgis-plugin-ci](../.qgis-plugin-ci) to use Transifex translation.

If you want to see the translations during development, add `i18n` to the `extra_dirs` in `build.py`:

```python
extra_dirs = ["resources", "i18n"]
```

#### Pushing / creating new translations

For step-by-step instructions, read the [translation tutorial](./translation_tutorial.md#Tutorial).

* First, install [Transifex CLI](https://docs.transifex.com/client/installing-the-client) and
  [qgis-plugin-ci](https://github.com/opengisch/qgis-plugin-ci)
* Make sure command `pylupdate5` works. Otherwise install it with `pip install pyqt5`
* Run `qgis-plugin-ci push-translation <your-transifex-token>`
* Go to your Transifex site, add some languages and start translating
* Copy [push_translations.yml](push_translations.yml) file to [workflows](../.github/workflows) folder to enable
  automatic pushing after commits to master
* Add this badge ![](https://github.com/j-osephlong/fieldwork-bakery/workflows/Translations/badge.svg) to
  the [README](../README.md)

##### Pulling

There is no need to pull if you configure `--transifex-token` into your
[release](../.github/workflows/release.yml) workflow (remember to use Github Secrets). Remember to uncomment the
lrelease section as well. You can however pull manually to test the process.

* Run `qgis-plugin-ci pull-translation --compile <your-transifex-token>`#### Translating with QT Linguistic (if Transifex not available)

The translation files are in [i18n](../fieldwork-bakery/resources/i18n) folder. Translatable content in python files is
code such as `tr(u"Hello World")`.

To update language *.ts* files to contain newest lines to translate, run

```shell script
python build.py transup
```

You can then open the *.ts* files you wish to translate with Qt Linguist and make the changes.

Compile the translations to *.qm* files with:

```shell script
python build.py transcompile
```


### Github Release

Follow these steps to create a release

* Add changelog information to [CHANGELOG.md](../CHANGELOG.md) using this
  [format](https://raw.githubusercontent.com/opengisch/qgis-plugin-ci/master/CHANGELOG.md)
* Make a new commit. (`git add -A && git commit -m "Release 0.1.0"`)
* Create new tag for it (`git tag -a 0.1.0 -m "Version 0.1.0"`)
* Push tag to Github using `git push --follow-tags`
* Create Github release
* [qgis-plugin-ci](https://github.com/opengisch/qgis-plugin-ci) adds release zip automatically as an asset

Modify [release](../.github/workflows/release.yml) workflow according to its comments if you want to upload the
plugin to QGIS plugin repository.

### Local release

For local release install [qgis-plugin-ci](https://github.com/opengisch/qgis-plugin-ci) (possibly to different venv
to avoid Qt related problems on some environments) and follow these steps:
```shell
cd fieldwork-bakery
qgis-plugin-ci package --disable-submodule-update 0.1.0
```
