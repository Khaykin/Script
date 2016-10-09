#!/usr/bin
node {
    echo 'xara'
}
node {
   stage 'Stage 1'
   echo 'git checkout'
   echo 'JJOOPPAA JJOOPPAA JJOOPPAA'
}
//node {
    //sh 'echo AOEU=$(echo aoeu) > propsfile'
//}
node{
    stage 'Stage 2'
    gitClean()
    checkout([$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '1', url: 'git@github.com:ARMmbed/ta-DxHDCP.git']]])
    echo 'git cleaned'
}
/**
 * Clean a Git project workspace.
 * Uses 'git clean' if there is a repository found.
 * Uses Pipeline 'deleteDir()' function if no .git directory is found.
 */
def gitClean() {
    timeout(time: 60, unit: 'SECONDS') {
        if (fileExists('.git')) {
            echo 'Found Git repository: using Git to clean the tree.'
            // The sequence of reset --hard and clean -fdx first
            // in the root and then using submodule foreach
            // is based on how the Jenkins Git SCM clean before checkout
            // feature works.
            sh 'git reset --hard'
            // Note: -e is necessary to exclude the temp directory
            // .jenkins-XXXXX in the workspace where Pipeline puts the
            // batch file for the 'bat' command.
            sh 'git clean -ffdx -e ".jenkins-*/"'
            sh 'git submodule foreach --recursive git reset --hard'
            sh 'git submodule foreach --recursive git clean -ffdx'
        }
        else
        {
            echo 'No Git repository found: using deleteDir() to wipe clean'
            deleteDir()
        }
    }
}
echo 'build'


node {
    sh './Scripts/build_hdcp_and_tests.py -p Qualcomm -m MSM8996_LA2.0 -v 01450.1 -c yes'
}
echo 'HDCP buil finished'

node {
    stage 'Stage 5'
    mail bcc: '', body: 'build HDCP finished for MSM8996_LA2.0 -v 01450.1 !!!', cc: '', from: '', replyTo: '', subject: 'HDCP master builded', to: 'igor.haykin@sansasecurity.com'
}
