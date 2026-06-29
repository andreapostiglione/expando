#import <Cocoa/Cocoa.h>
#import <Sparkle/Sparkle.h>

@interface ExpandoSparkleDelegate : NSObject <NSApplicationDelegate, SPUUpdaterDelegate>
@property(nonatomic, strong) SPUStandardUpdaterController *controller;
@property(nonatomic, assign) BOOL interactive;
@end

@implementation ExpandoSparkleDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    self.controller = [[SPUStandardUpdaterController alloc] initWithUpdaterDelegate:self
                                                               userDriverDelegate:nil];
    if (self.interactive) {
        [self.controller.updater checkForUpdates];
    } else {
        [self.controller.updater checkForUpdatesInBackground];
    }
}

- (void)updater:(SPUUpdater *)updater didFinishUpdateCycleForUpdateCheck:(SPUUpdateCheck)updateCheck
          error:(NSError *)error {
    if (!self.interactive) {
        [NSApp terminate:nil];
    }
}

@end

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        BOOL interactive = (argc > 1 && strcmp(argv[1], "interactive") == 0);
        ExpandoSparkleDelegate *delegate = [[ExpandoSparkleDelegate alloc] init];
        delegate.interactive = interactive;
        NSApplication *application = [NSApplication sharedApplication];
        [application setActivationPolicy:NSApplicationActivationPolicyAccessory];
        application.delegate = delegate;
        [application run];
    }
    return 0;
}
