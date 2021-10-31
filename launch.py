import argparse
from magicgui import magicgui
import napari
from magicgui.widgets import RadioButtons, Container
from pcna_viewer import PCNA_Viewer


@magicgui(labels=False,
          auto_call=True,
          result_widget=True,
          rev={
              "widget_type": "PushButton",
              "text": "Revert",
          })
def revert(rev):
    global viewer
    msg = viewer.revert()
    viewer.refresh()
    return msg


@magicgui(labels=False,
          auto_call=True,
          result_widget=True,
          sv={
              "widget_type": "PushButton",
              "text": "Save",
          })
def save(sv):
    global viewer
    msg = viewer.save()
    return msg


@magicgui(labels=True, result_widget=True)
def create_or_replace(track_A: int, track_B: int=0, frame: int=0):
    global viewer
    if track_B < 1:
        track_B = None
    msg = viewer.create_or_replace(track_A, frame, track_B)
    viewer.refresh()
    return msg


@magicgui(labels=True, result_widget=True)
def delete(track: int, frame: int=0):
    global viewer
    if frame < 1:
        frame = None
    msg = viewer.delete_track(track, frame)
    viewer.refresh()
    return msg

@magicgui(labels=True, result_widget=True)
def max_label(frame: int):
    global viewer
    msg = viewer.get_mx(frame)
    viewer.refresh()
    return msg

@magicgui(labels=True,
          result_widget=True,
          mode={
              'widget_type': 'RadioButtons',
              'orientation': 'vertical',
              'choices': [(' to next transition', 1), (' single frame', 2), (' to end frame', 3)]
          },
          phase={
              'widget_type': 'RadioButtons',
              'orientation': 'horizontal',
              'choices': [('G1', 1), ('S', 2), ('G2', 3), ('M', 4)]
          })
def phase(track: int, frame_start: int, frame_end: int, phase=1, mode=1):
    global viewer
    phase_rev = {1: 'G1', 2: 'S', 3: 'G2', 4: 'M'}
    mode_rev = {1: 'to_next', 2: 'single', 3: 'range'}
    if mode == 3:
        msg = viewer.correct_cls(track, frame_start, phase_rev[phase], mode_rev[mode], frame_end)
    else:
        msg = viewer.correct_cls(track, frame_start, phase_rev[phase], mode_rev[mode])
    viewer.refresh()
    return msg


@magicgui(labels=True, result_widget=True)
def create_par(mother: int, daughter: int):
    global viewer
    msg = viewer.create_parent(mother, daughter)
    viewer.refresh()
    return msg


@magicgui(labels=True, result_widget=True)
def delete_par(daughter: int):
    global viewer
    msg = viewer.del_parent(daughter)
    viewer.refresh()
    return msg


@magicgui(labels=True,
          result_widget=True,
          phase={
              'widget_type': 'RadioButtons',
              'orientation': 'horizontal',
              'choices': [('G1', 1), ('S', 2), ('G2', 3), ('M', 4)]
          })
def register_obj(object_ID: int, frame: int, track: int, phase=1):
    global viewer
    phase_rev = {1: 'G1', 2: 'S', 3: 'G2', 4: 'M'}
    msg = viewer.register_obj(object_ID, frame, track, phase_rev[phase])
    viewer.refresh()
    return msg


def get_parser():
    parser = argparse.ArgumentParser(description="pcnaDeep script for visualisation and correction.")
    parser.add_argument(
        "--track",
        metavar="FILE",
        help="path to tracked object table csv file",
    )
    parser.add_argument(
        "--mask",
        metavar="FILE",
        help="path to mask file",
    )
    parser.add_argument(
        "--image",
        metavar="FILE",
        help="path to composite image file",
    )
    parser.add_argument(
        "--pcna",
        metavar="FILE",
        help="path to PCNA image file, if composite is not supplied",
    )
    parser.add_argument(
        "--bf",
        metavar="FILE",
        help="path to bright field image file, if composite is not supplied",
    )
    parser.add_argument(
        "--sat",
        default=1,
        help="pixel saturation to rescale PCNA and BF, not apply to composite input",
    )
    parser.add_argument(
        "--gamma",
        default=1,
        help="gamma factor to rescale PCNA, not apply to composite input.",
    )
    return parser


if __name__ == '__main__':
    btns = RadioButtons(name='',
                        choices=[(" Replace track A with B or \n Create track from certain frame", 1),
                                 (" Delete track", 2),
                                 (" Edit cell cycle phase", 3), (" Link mother - daughter", 4),
                                 (" Unlink mother - daughter", 5), (" Register object", 6),
                                 (' Get max object label', 7)],
                        orientation='vertical',
                        label='',
                        )
    btns.value = 1


    @btns.changed.connect
    def _toggle_visibility(value: str):
        # helps to avoid a flicker
        for x in [create_or_replace, delete, phase, create_par, delete_par, register_obj, max_label]:
            x.visible = False
        create_or_replace.visible = value == 1
        delete.visible = value == 2
        phase.visible = value == 3
        create_par.visible = value == 4
        delete_par.visible = value == 5
        register_obj.visible = value == 6
        max_label.visible = value == 7


    container_opt = Container(widgets=[btns, create_or_replace, delete, phase, create_par, delete_par, register_obj, max_label],
                              layout='vertical',
                              labels=False)
    container_opt.margins = (0, 0, 0, 0)
    container_but = Container(widgets=[revert, save],
                              layout='horizontal',
                              labels=False)
    container_but.margins = (0, 0, 0, 0)
    container_ext = Container(widgets=[container_opt, container_but],
                              layout='vertical')
    container_ext.margins = (5, 5, 5, 5)
    # container.show(run=True)

    # Create the viewer
    args = get_parser().parse_args()
    if args.image is not None:
        viewer = PCNA_Viewer(track_path=args.track,
                            comp_path=args.image,
                            mask_path=args.mask,
                            frame_base=0)
    elif args.pcna is not None and args.bf is not None:
        viewer = PCNA_Viewer(track_path=args.track,
                            pcna_path=args.pcna,
                            bf_path=args.bf,
                            mask_path=args.mask,
                            frame_base=0,
                            sat=float(args.sat),
                            gamma=float(args.gamma))
    else:
        raise argparse.ArgumentError('Not enough image file input!')

    # Add plugin to the napari viewer
    viewer.window.add_dock_widget(container_ext, area='left')
    # Update the layer dropdown menu when the layer list changes
    viewer.layers.events.changed.connect(container_ext.reset_choices)

    napari.run()
