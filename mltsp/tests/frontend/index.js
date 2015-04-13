casper.test.begin('index loads', 1, function suite(test) {
    casper.start('http://localhost:5000', function() {
        test.assertTextExists('Sign in with your Google Account',
                              'Authentication displayed on index page');
    });

    casper.run(function() {
        test.done();
    });
});
