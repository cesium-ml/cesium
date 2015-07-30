casper.test.begin('create new project'
                  /*, planned nr of tests, */,  function suite(test) {
    casper.start('http://localhost:5000', function() {

        casper.then(function(){
            test.assertTextExists('ML Time-Series Platform',
                                  'Loaded post-auth index page');
        });
        casper.then(function(){
            this.fill('form#newProjectForm', {
                'new_project_name': 'test_name',
                'project_description': 'desc',
                'addl_authed_users': ''
            }, true);
            this.click('#new_project_button');
        });
        casper.then(function(){
            test.assertTextExists('New project successfully created',
                                  'Successfully created new project');
        });
    });
    casper.run(function() {
        test.done();
    });
});
