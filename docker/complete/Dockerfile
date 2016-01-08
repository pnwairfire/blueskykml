# Container to run blueskykml
FROM blueskykml-base

RUN pip install --no-binary gdal --trusted-host pypi.smoke.airfire.org -i http://pypi.smoke.airfire.org/simple blueskykml

### To install from github instead of from AirFire's pypi server
#RUN pip install --no-binary gdal https://github.com/pnwairfire/blueskykml/archive/master.tar.gz

CMD ["makedispersionkml", "-h"]
