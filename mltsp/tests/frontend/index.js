casper.test.begin('index loads', 1, function suite(test) {
    casper.start('http://localhost:5000', function() {
        test.assertTextExists('MLTSP', 'successfully loaded index page');
    });

    casper.run(function() {
        test.done();
    });
});
