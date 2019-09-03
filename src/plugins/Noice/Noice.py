from Deadline.Plugins import *
from System.Diagnostics import *
import re
import os.path


def __main__(*args):
    # Do test stuff
    pass


def GetDeadlinePlugin():
    return NoicePlugin()


def CleanupDeadlinePlugin(plugin):
    plugin.cleanup()


class NoicePlugin (DeadlinePlugin):
    def __init__(self):
        self.InitializeProcessCallback += self.initialize_process
        self.RenderExecutableCallback += self.render_executable
        self.RenderArgumentCallback += self.render_argument

    def cleanup():
        for handler in self.StdoutHandlers:
            del handler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback

    def initialize_process(self):
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Simple

        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.StdoutHandling = True
        self.PopupHandling = False

        self.AddStdoutHandlerCallback('ERROR:(.*)').HandleCallback += self.handle_stdout_error

    def handle_stdout_error(self):
        self.FailRender('Detected an error: ' + self.GetRegexMatch(1))

    # Figure out how to get the number of times this has been called
    def handle_stdout_progress(self):
        self.SetProgress(self.GetJob().GetJobInfoKeyValue('ChunkSize'))

    def render_executable(self):
        return self.GetConfigEntry('NoiceRenderExecutable')

    def render_argument(self):
        start = self.GetStartFrame()
        end = self.GetEndFrame()

        arguments = '--input {0} --output {1} --frames {2} --extraframes {3} '\
                    '--patchradius {4} --searchradius {5} --variance {6} {7}'
        arguments = arguments.format(
            self.path_for_frame(self.GetPluginInfoEntry('InputPattern'), start),
            self.path_for_frame(self.GetPluginInfoEntry('OutputPattern'), start),
            end - start + 1,
            self.GetIntegerPluginInfoEntry('ExtraFrames'),
            self.GetIntegerPluginInfoEntry('PatchRadius'),
            self.GetIntegerPluginInfoEntry('SearchRadius'),
            self.GetFloatPluginInfoEntry('Variance'),
            self.aovs())

        return arguments

    def aovs(self):
        aovs = self.GetPluginInfoEntry('AOV').strip()
        if len(aovs) > 0:
            return ''.join(['--aov {0} '.format(aov) for aov in aovs.split(' ')])
        else:
            return ''

    def path_for_frame(self, path, frame):
        directory, filename = os.path.split(path)
        match = re.match(r'(.*\.)([#\d]+)(\.exr)', filename)
        filename = self.filename_for_frame(match, frame) if match else filename
        return os.path.join(directory, filename)

    def filename_for_frame(self, match, frame):
        head = match.group(1)
        frame_pattern = match.group(2)
        extension = match.group(3)
        frame_padded = str(frame).zfill(len(frame_pattern))
        return '{0}{1}{2}'.format(head, frame_padded, extension)
