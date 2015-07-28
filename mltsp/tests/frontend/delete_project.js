casper.test.begin('delete_project'
                  /*, planned nr of tests, */,  function suite(test) {
    casper.start('http://localhost:5000', function() {
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

        // See if #editOrDeleteSubmit exists
        casper.then(function() {
            test.assertExists("#editOrDeleteSubmit",
                              "#editOrDeleteSubmit selector exists");
        });


        // Fill form and click submit button
        casper.then(function(){
            this.fill('form#newProjectForm', {
                'new_project_name': 'test_name',
                'project_description': 'desc',
                'addl_authed_users': ''
            }, false);
            this.click('#new_project_button');
        });

        // Assert pop-up dialog exists with success message & click ok
        casper.then(function() {
            casper.waitForSelector("#new-project-dialog-ok-btn", function(){
                test.assertTextExists('New project successfully created',
                                      'Successfully created new project');
                this.click('#new-project-dialog-ok-btn');
            });
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
                test.assertTextExists('Deleted 1 project(s).',
                                      'Got success message (in jQuery dialog)');
                this.click("#editDeleteResultsDialog-okbtn");
            });
        });

    });

    casper.run(function() {
        test.done();
    });
});
