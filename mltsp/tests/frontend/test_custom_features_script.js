casper.test.begin('test_custom_features_script', function suite(test) {
    casper.start('http://localhost:5000', function() {
        this.page.viewportSize = { width: 1920, height: 1080 };
        test.assertTextExists('Please log in',
                              'Authentication displayed on index page');
        this.test.assertExists('form.login-form', 'Login form found');
        this.fill('form.login-form', {
            'login': 'testhandle@test.com',
            'password':  'TestPass15'
        }, true);

        casper.setFilter("page.confirm", function(message) {
            this.echo(message);
            return message === "Delete selected project?" ? true : false;
        });

        casper.then(function(){
            this.click("#feature_selection_link");
        });

        casper.then(function(){
            this.page.uploadFile('#custom_feat_script_file',
                                 'mltsp/tests/data/testfeature1.py');
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

    casper.run(function() {
        test.done();
    });
});
