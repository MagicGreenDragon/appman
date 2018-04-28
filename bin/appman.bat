@echo off

 :: Copyright (C) 2018  Daniele Giudice
 :: This program is free software: you can redistribute it and/or modify
 :: it under the terms of the GNU General Public License as published by
 :: the Free Software Foundation, either version 3 of the License, or
 :: (at your option) any later version.
 :: This program is distributed in the hope that it will be useful,
 :: but WITHOUT ANY WARRANTY; without even the implied warranty of
 :: MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 :: GNU General Public License for more details.
 :: You should have received a copy of the GNU General Public License
 :: along with this program.  If not, see <http://www.gnu.org/licenses/>.

 :: Run AppMan using embed python
%~dp0\python-embed\python -B %~dp0\..\appman.py %*

 :: Refresh Environment Varialbes on current cmd (not work in powershell)
call RefreshEnv.bat > NUL 2>&1