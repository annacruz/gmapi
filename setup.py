from distutils.core import setup
import os


# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('gmapi'):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)
    elif filenames:
        prefix = dirpath[6:] # Strip "gmapi/" or "gmapi\"
        for f in filenames:
            data_files.append(os.path.join(prefix, f))


setup(name='gmapi',
      version='0.1',
      description='A Google Maps API implementation',
      author='Anna Cruz',
      author_email='anna.cruz@gmail.com',
      url='',
      packages=packages,
      package_data={'gmapi': data_files},
      classifiers=[],
      )
