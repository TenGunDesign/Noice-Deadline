from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog
from Deadline.Scripting import *
import os
import re

from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *


dialog = None
row = 0
writer_info = ""


def __main__():
    global dialog
    dialog = DeadlineScriptDialog()
    dialog.SetTitle("Submit Noice Job to Deadline")
    standard_options()
    plugin_options()
    buttons()
    dialog.ShowDialog(True)


def plugin_options():
    global dialog
    dialog.AddGrid()
    dialog.AddControlToGrid("Separator3", "SeparatorControl", "Noice Options", next_row(), 0, colSpan=3)
    field("InputPattern",
          "Input pattern",
          "Full file path for first frame of the sequence to denoise",
          browser=True).ValueModified.connect(autofill_from_input_pattern)
    field("OutputPattern",
          "Output pattern",
          "Full file path for the first frame of output",
          browser=True, new=True)
    field("Frames",
          "Frames list",
          "Which frames to denoise",
          "1")
    field("ChunkSize",
          "Frames per task",
          "How many frames should be rendered in each task",
          1, (1, 10000), True)
    field("ExtraFrames",
          "Extra frames",
          "Number of frames to pad before and after for temporal stability",
          0, (0, 2), True)
    field("PatchRadius",
          "Patch radius",
          "Neighborhood patch radius, size of pixel neighborhood to compare",
          3, (0, 6), True)
    field("SearchRadius",
          "Search radius",
          "Search radius, higher values mean a wider search for similar pixel neighborhoods",
          9, (6, 21), True)
    field("Variance",
          "Variance",
          "Variance threshold, higher values mean more aggressive denoising",
          0.25, (0.0, 1.0))
    field("AOV",
          "AOVs",
          "Space-separated list of light AOVs to be co-denoised")
    dialog.EndGrid()


def buttons():
    global dialog
    reset_row()
    dialog.AddGrid()
    dialog.AddHorizontalSpacerToGrid("DummyLabel", 0, 0)
    button("OK", handle_ok)
    button("Cancel", handle_cancel)
    dialog.EndGrid()


def field(name, label, hover, default=None, numeric_range=None, integer=False, browser=False, new=False):
    global dialog
    row = next_row()
    label_name = "{0}_label".format(name)
    dialog.AddControlToGrid(label_name, "LabelControl", label, row, 0, hover, expand=False)
    if numeric_range:
        minimum, maximum = numeric_range
        decimal_places = 0 if integer else 2
        increment = 1 if integer else 0.05
        return dialog.AddRangeControlToGrid(name, "RangeControl", default, minimum, maximum, decimal_places, increment, row, 1, colSpan=3)
    elif browser:
        kind = "FileSaverControl" if new else "FileBrowserControl"
        return dialog.AddSelectionControlToGrid(name, kind, default if default else "", "EXR (*.exr)", row, 1, colSpan=3)
    else:
        return dialog.AddControlToGrid(name, "TextControl", default if default else "", row, 1, colSpan=3)


def button(label, callback):
    global dialog
    button = dialog.AddControlToGrid(label, "ButtonControl", label, 0, next_row(), expand=False)
    button.ValueModified.connect(callback)
    return button


def autofill_from_input_pattern():
    populate_frame_list()
    populate_output_path()


# Rudimentary, just uses the smallest and greatest frame numbers that match the pattern
def populate_frame_list():
    directory, file = os.path.split(dialog.GetValue("InputPattern"))
    pattern = re.compile(r".*\.(\d+)\.exr")
    matches = [pattern.match(item) for item in os.listdir(directory)]
    frames = [int(match.group(1)) for match in matches if match is not None]
    if len(frames) > 1:
        frame_range = "{0}-{1}".format(frames[0], frames[-1])
        dialog.SetValue("Frames", frame_range)
    elif len(frames) > 0:
        dialog.SetValue("Frames", str(frames[0]))


def populate_output_path():
    input_pattern = dialog.GetValue("InputPattern")
    pattern = re.compile(r"(.*\d+)\.exr")
    match = pattern.match(input_pattern)
    if match is not None:
        output_pattern = "{0}_denoised.exr".format(match.group(1))
        dialog.SetValue("OutputPattern", output_pattern)


def next_row():
    global row
    current = row
    row += 1
    return current


def reset_row():
    global row
    row = 0


def handle_cancel():
    close_dialog()


def handle_ok():
    if valid_options():
        job_info = create_job_options()
        plugin_info = create_plugin_options()
        submit_job(job_info, plugin_info)


def close_dialog():
    global dialog
    dialog.CloseDialog()


def create_plugin_options():
    global dialog, writer_info
    filename = os.path.join(ClientUtils.GetDeadlineTempPath(), "noice_plugin_info.job")
    writer = StreamWriter(filename, False, Encoding.Unicode)
    writer_info = (writer, filename)
    add_line("InputPattern")
    add_line("OutputPattern")
    add_line("ExtraFrames")
    add_line("PatchRadius")
    add_line("SearchRadius")
    add_line("Variance")
    add_line("AOV")
    writer.Close()
    return filename


def add_line(control):
    global dialog, writer_info
    writer, _ = writer_info
    writer.WriteLine("{0}={1}".format(control, dialog.GetValue(control)))


def submit_job(job_info, plugin_info):
    global dialog
    arguments = StringCollection()
    arguments.Add(job_info)
    arguments.Add(plugin_info)

    results = ClientUtils.ExecuteCommandAndGetOutput(arguments)
    dialog.ShowMessageBox(results, "Submission Results")


def valid_options():
    global dialog

    inputFile = dialog.GetValue("InputPattern").strip()
    if not FileUtils.FileExists(inputFile):
        dialog.ShowMessageBox("The input pattern does not exist")
        return False

    outputFile = dialog.GetValue("OutputPattern").strip()
    outputDir, _ = os.path.split(outputFile)
    if (not os.path.isdir(outputDir)):
        dialog.ShowMessageBox("The output directory does not exist: " + outputDir, "Error")
        return False
    elif (PathUtils.IsPathLocal(outputFile)):
        result = dialog.ShowMessageBox("The output file " + outputFile + " is local, are you sure you want to continue?", "Warning", ("Yes", "No"))
        if (result == "No"):
            return False

    frames = dialog.GetValue("Frames")
    if (not FrameUtils.FrameRangeValid(frames)):
        dialog.ShowMessageBox("Frame range {0} is not valid".format(frames, "Error"))
        return False

    return True


def create_job_options():
    global dialog

    filename = os.path.join(ClientUtils.GetDeadlineTempPath(), "noice_job_info.job")
    writer = StreamWriter(filename, False, Encoding.Unicode)
    writer.WriteLine("Plugin=Noice")
    writer.WriteLine("Name={0}".format(dialog.GetValue("NameBox")))
    writer.WriteLine("Comment={0}".format(dialog.GetValue("CommentBox")))
    writer.WriteLine("Department={0}".format(dialog.GetValue("DepartmentBox")))
    writer.WriteLine("Pool={0}".format(dialog.GetValue("PoolBox")))
    writer.WriteLine("SecondaryPool={0}".format(dialog.GetValue("SecondaryPoolBox")))
    writer.WriteLine("Group={0}".format(dialog.GetValue("GroupBox")))
    writer.WriteLine("Priority={0}".format(dialog.GetValue("PriorityBox")))
    writer.WriteLine("TaskTimeoutMinutes={0}".format(dialog.GetValue("TaskTimeoutBox")))
    writer.WriteLine("EnableAutoTimeout={0}".format(dialog.GetValue("AutoTimeoutBox")))
    writer.WriteLine("ConcurrentTasks={0}".format(dialog.GetValue("ConcurrentTasksBox")))
    writer.WriteLine("LimitConcurrentTasksToNumberOfCpus={0}".format(dialog.GetValue("LimitConcurrentTasksBox")))
    writer.WriteLine("ChunkSize={0}".format(dialog.GetValue("ChunkSize")))

    writer.WriteLine("MachineLimit={0}".format(dialog.GetValue("MachineLimitBox")))
    if(bool(dialog.GetValue("IsBlacklistBox"))):
        writer.WriteLine("Blacklist={0}".format(dialog.GetValue("MachineListBox")))
    else:
        writer.WriteLine("Whitelist={0}".format(dialog.GetValue("MachineListBox")))

    writer.WriteLine("LimitGroups={0}".format(dialog.GetValue("LimitGroupBox")))
    writer.WriteLine("JobDependencies={0}".format(dialog.GetValue("DependencyBox")))
    writer.WriteLine("OnJobComplete={0}".format(dialog.GetValue("OnJobCompleteBox")))

    if(bool(dialog.GetValue("SubmitSuspendedBox"))):
        writer.WriteLine("InitialStatus=Suspended")

    writer.WriteLine("Frames={0}".format(dialog.GetValue("Frames")))
    writer.WriteLine("ChunkSize=1")

    writer.Close()
    return filename


def standard_options():
    global dialog
    dialog.AddGrid()
    dialog.AddControlToGrid("Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=2)

    dialog.AddControlToGrid("NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False)
    dialog.AddControlToGrid("NameBox", "TextControl", "Untitled", 1, 1)

    dialog.AddControlToGrid("CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False)
    dialog.AddControlToGrid("CommentBox", "TextControl", "", 2, 1)

    dialog.AddControlToGrid("DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False)
    dialog.AddControlToGrid("DepartmentBox", "TextControl", "", 3, 1)
    dialog.EndGrid()

    dialog.AddGrid()
    dialog.AddControlToGrid("Separator2", "SeparatorControl", "Job Options", 0, 0, colSpan=3)

    dialog.AddControlToGrid("PoolLabel", "LabelControl", "Pool", 1, 0, "The pool that your job will be submitted to.", False)
    dialog.AddControlToGrid("PoolBox", "PoolComboControl", "none", 1, 1)

    dialog.AddControlToGrid("SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False)
    dialog.AddControlToGrid("SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1)

    dialog.AddControlToGrid("GroupLabel", "LabelControl", "Group", 3, 0, "The group that your job will be submitted to.", False)
    dialog.AddControlToGrid("GroupBox", "GroupComboControl", "none", 3, 1)

    dialog.AddControlToGrid("PriorityLabel", "LabelControl", "Priority", 4, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False)
    dialog.AddRangeControlToGrid("PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 4, 1)

    dialog.AddControlToGrid("TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False)
    dialog.AddRangeControlToGrid("TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1)
    dialog.AddSelectionControlToGrid("AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job. ")

    dialog.AddControlToGrid("ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 6, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False)
    dialog.AddRangeControlToGrid("ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 6, 1)
    dialog.AddSelectionControlToGrid("LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 6, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator.")

    dialog.AddControlToGrid("MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False)
    dialog.AddRangeControlToGrid("MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1)
    dialog.AddSelectionControlToGrid("IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist.")

    dialog.AddControlToGrid("MachineListLabel", "LabelControl", "Machine List", 8, 0, "The whitelisted or blacklisted list of machines.", False)
    dialog.AddControlToGrid("MachineListBox", "MachineListControl", "", 8, 1, colSpan=2)

    dialog.AddControlToGrid("LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False)
    dialog.AddControlToGrid("LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=2)

    dialog.AddControlToGrid("DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False)
    dialog.AddControlToGrid("DependencyBox", "DependencyControl", "", 10, 1)

    dialog.AddControlToGrid("OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes.", False)
    dialog.AddControlToGrid("OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1)
    dialog.AddSelectionControlToGrid("SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render.", False)
    dialog.EndGrid()
