casper.test.begin('test custom features script', function suite(test) {
    var system = require('system');
    var env = system.env;
    if (casper.cli.get('with-docker')) {
        casper.start('http://localhost:5000', function() {
            this.page.viewportSize = { width: 1920, height: 1080 };

            casper.then(function(){
                this.click("#feature_selection_link");
            });

            casper.then(function(){
                this.page.uploadFile('#custom_feat_script_file',
                                     'cesium/tests/data/testfeature1.py');
            });
            casper.then(function(){
                this.click('#custom_feats_file_submit_button');
            });

            casper.then(function() {
                casper.waitForText("The following features have successfully been tested:",
                                   function(){
                    test.assertTextExists('avg_mag',
                                          'Successfully tested new script');
                });
            });

        });
    } else {
        casper.log('--with-docker not specified, skipping');
    }

    casper.run(function() {
        test.done();
    });
});
