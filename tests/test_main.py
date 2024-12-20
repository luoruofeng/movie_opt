from movie_opt.main import main
import sys

def test_command_a(capsys):
    sys.argv = ["C:\\Users\luoruofeng\\miniconda3\\envs\\movie\\Scripts\\movie_opt.exe", "create","phone", "--path", "Test"]
    main()
    captured = capsys.readouterr()
    assert "Hello, Test!" in captured.out
