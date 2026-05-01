import subprocess
import sys

REMOTE = 'https://github.com/snehakm123/certifyme-task'

def run(cmd):
    print('>',' '.join(cmd))
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(r.stdout)
    return r.returncode

def main():
    run(['git', 'init'])
    run(['git', 'add', '.'])
    run(['git', 'commit', '-m', 'Initial import: add backend Flask app and UI'])
    run(['git', 'branch', '-M', 'main'])
    code = run(['git', 'remote', 'add', 'origin', REMOTE])
    if code != 0:
        run(['git', 'remote', 'set-url', 'origin', REMOTE])
    print('Pushing to remote...')
    code = run(['git', 'push', '-u', 'origin', 'main'])
    if code != 0:
        print('Push may have failed or requires authentication. Please run the following commands locally:')
        print('  git remote add origin ' + REMOTE)
        print('  git push -u origin main')
        sys.exit(code)
    print('Push finished.')

if __name__ == '__main__':
    main()
