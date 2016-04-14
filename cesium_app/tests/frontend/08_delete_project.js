casper.test.begin('delete project'
                  /*, planned nr of tests, */,  function suite(test) {
    casper.start('http://localhost:5000', function() {

        casper.setFilter("page.confirm", function(message) {
            this.echo(message);
            return message === "Delete selected project?" ? true : false;
        });

        // Wait for page to reload & delete new project
        casper.then(function(){

            this.evaluate(function() {
                document.querySelector('#action').selectedIndex = 1;
                document.querySelector('#PROJECT_NAME_TO_EDIT').selectedIndex = 0;
                return true;
            });
            this.click('#editOrDeleteSubmit');
        });

        casper.then(function(){
            casper.waitForSelector("#editDeleteResultsDialog-okbtn", function(){
                test.assertTextExists('Deleted',
                                      'Got success message (in jQuery dialog)');
                this.click("#editDeleteResultsDialog-okbtn");
            });
        });

    });

    casper.run(function() {
        test.done();
    });
});
